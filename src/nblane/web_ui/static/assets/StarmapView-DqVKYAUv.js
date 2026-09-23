var Bg=Object.defineProperty;var kg=(n,e,t)=>e in n?Bg(n,e,{enumerable:!0,configurable:!0,writable:!0,value:t}):n[e]=t;var Ie=(n,e,t)=>kg(n,typeof e!="symbol"?e+"":e,t);import{u as zg,r as gi,j as Bt,L as Gg}from"./index-X_f7-nZy.js";/**
 * @license
 * Copyright 2010-2026 Three.js Authors
 * SPDX-License-Identifier: MIT
 */const qa="184",Ps={ROTATE:0,DOLLY:1,PAN:2},As={ROTATE:0,PAN:1,DOLLY_PAN:2,DOLLY_ROTATE:3},Hg=0,jf=1,Vg=2,Vo=1,Wg=2,ya=3,Xi=0,sn=1,wn=2,Sn=0,zr=1,nl=2,Kf=3,Zf=4,Xg=5,Nr=100,Yg=101,qg=102,jg=103,Kg=104,Zg=200,$g=201,Jg=202,Qg=203,Su=204,bu=205,e_=206,t_=207,n_=208,i_=209,r_=210,s_=211,a_=212,o_=213,l_=214,yu=0,il=1,Tu=2,Ns=3,Eu=4,wu=5,Au=6,Ru=7,um=0,c_=1,u_=2,Pi=0,hm=1,fm=2,dm=3,pm=4,mm=5,gm=6,_m=7,vm=300,jr=301,Os=302,tc=303,nc=304,Al=306,Cu=1e3,Hi=1001,Pu=1002,cn=1003,h_=1004,so=1005,zt=1006,ic=1007,Br=1008,Yt=1009,xm=1010,Mm=1011,Oa=1012,Hh=1013,Di=1014,li=1015,Yi=1016,Vh=1017,Wh=1018,Bs=1020,Sm=35902,bm=35899,ym=1021,Tm=1022,ci=1023,qi=1026,cr=1027,Em=1028,Xh=1029,Kr=1030,Yh=1031,qh=1033,Wo=33776,Xo=33777,Yo=33778,qo=33779,Du=35840,Uu=35841,Lu=35842,Iu=35843,Fu=36196,Nu=37492,Ou=37496,Bu=37488,ku=37489,rl=37490,zu=37491,Gu=37808,Hu=37809,Vu=37810,Wu=37811,Xu=37812,Yu=37813,qu=37814,ju=37815,Ku=37816,Zu=37817,$u=37818,Ju=37819,Qu=37820,eh=37821,th=36492,nh=36494,ih=36495,rh=36283,sh=36284,sl=36285,ah=36286,ja=3200,f_=3201,$f=0,d_=1,yi="",bt="srgb",ks="srgb-linear",al="linear",xt="srgb",as=7680,Jf=519,p_=512,m_=513,g_=514,jh=515,__=516,v_=517,Kh=518,x_=519,oh=35044,Qf="300 es",Ai=2e3,ol=2001;function M_(n){for(let e=n.length-1;e>=0;--e)if(n[e]>=65535)return!0;return!1}function ll(n){return document.createElementNS("http://www.w3.org/1999/xhtml",n)}function S_(){const n=ll("canvas");return n.style.display="block",n}const ed={};function cl(...n){const e="THREE."+n.shift();console.log(e,...n)}function wm(n){const e=n[0];if(typeof e=="string"&&e.startsWith("TSL:")){const t=n[1];t&&t.isStackTrace?n[0]+=" "+t.getLocation():n[1]='Stack trace not available. Enable "THREE.Node.captureStackTrace" to capture stack traces.'}return n}function $e(...n){n=wm(n);const e="THREE."+n.shift();{const t=n[0];t&&t.isStackTrace?console.warn(t.getError(e)):console.warn(e,...n)}}function ft(...n){n=wm(n);const e="THREE."+n.shift();{const t=n[0];t&&t.isStackTrace?console.error(t.getError(e)):console.error(e,...n)}}function lh(...n){const e=n.join(" ");e in ed||(ed[e]=!0,$e(...n))}function b_(n,e,t){return new Promise(function(r,i){function s(){switch(n.clientWaitSync(e,n.SYNC_FLUSH_COMMANDS_BIT,0)){case n.WAIT_FAILED:i();break;case n.TIMEOUT_EXPIRED:setTimeout(s,t);break;default:r()}}setTimeout(s,t)})}const y_={[yu]:il,[Tu]:Au,[Eu]:Ru,[Ns]:wu,[il]:yu,[Au]:Tu,[Ru]:Eu,[wu]:Ns};class hi{addEventListener(e,t){this._listeners===void 0&&(this._listeners={});const r=this._listeners;r[e]===void 0&&(r[e]=[]),r[e].indexOf(t)===-1&&r[e].push(t)}hasEventListener(e,t){const r=this._listeners;return r===void 0?!1:r[e]!==void 0&&r[e].indexOf(t)!==-1}removeEventListener(e,t){const r=this._listeners;if(r===void 0)return;const i=r[e];if(i!==void 0){const s=i.indexOf(t);s!==-1&&i.splice(s,1)}}dispatchEvent(e){const t=this._listeners;if(t===void 0)return;const r=t[e.type];if(r!==void 0){e.target=this;const i=r.slice(0);for(let s=0,a=i.length;s<a;s++)i[s].call(this,e);e.target=null}}}const fn=["00","01","02","03","04","05","06","07","08","09","0a","0b","0c","0d","0e","0f","10","11","12","13","14","15","16","17","18","19","1a","1b","1c","1d","1e","1f","20","21","22","23","24","25","26","27","28","29","2a","2b","2c","2d","2e","2f","30","31","32","33","34","35","36","37","38","39","3a","3b","3c","3d","3e","3f","40","41","42","43","44","45","46","47","48","49","4a","4b","4c","4d","4e","4f","50","51","52","53","54","55","56","57","58","59","5a","5b","5c","5d","5e","5f","60","61","62","63","64","65","66","67","68","69","6a","6b","6c","6d","6e","6f","70","71","72","73","74","75","76","77","78","79","7a","7b","7c","7d","7e","7f","80","81","82","83","84","85","86","87","88","89","8a","8b","8c","8d","8e","8f","90","91","92","93","94","95","96","97","98","99","9a","9b","9c","9d","9e","9f","a0","a1","a2","a3","a4","a5","a6","a7","a8","a9","aa","ab","ac","ad","ae","af","b0","b1","b2","b3","b4","b5","b6","b7","b8","b9","ba","bb","bc","bd","be","bf","c0","c1","c2","c3","c4","c5","c6","c7","c8","c9","ca","cb","cc","cd","ce","cf","d0","d1","d2","d3","d4","d5","d6","d7","d8","d9","da","db","dc","dd","de","df","e0","e1","e2","e3","e4","e5","e6","e7","e8","e9","ea","eb","ec","ed","ee","ef","f0","f1","f2","f3","f4","f5","f6","f7","f8","f9","fa","fb","fc","fd","fe","ff"],jo=Math.PI/180,ch=180/Math.PI;function pr(){const n=Math.random()*4294967295|0,e=Math.random()*4294967295|0,t=Math.random()*4294967295|0,r=Math.random()*4294967295|0;return(fn[n&255]+fn[n>>8&255]+fn[n>>16&255]+fn[n>>24&255]+"-"+fn[e&255]+fn[e>>8&255]+"-"+fn[e>>16&15|64]+fn[e>>24&255]+"-"+fn[t&63|128]+fn[t>>8&255]+"-"+fn[t>>16&255]+fn[t>>24&255]+fn[r&255]+fn[r>>8&255]+fn[r>>16&255]+fn[r>>24&255]).toLowerCase()}function at(n,e,t){return Math.max(e,Math.min(t,n))}function T_(n,e){return(n%e+e)%e}function rc(n,e,t){return(1-t)*n+t*e}function Ti(n,e){switch(e.constructor){case Float32Array:return n;case Uint32Array:return n/4294967295;case Uint16Array:return n/65535;case Uint8Array:return n/255;case Int32Array:return Math.max(n/2147483647,-1);case Int16Array:return Math.max(n/32767,-1);case Int8Array:return Math.max(n/127,-1);default:throw new Error("Invalid component type.")}}function Mt(n,e){switch(e.constructor){case Float32Array:return n;case Uint32Array:return Math.round(n*4294967295);case Uint16Array:return Math.round(n*65535);case Uint8Array:return Math.round(n*255);case Int32Array:return Math.round(n*2147483647);case Int16Array:return Math.round(n*32767);case Int8Array:return Math.round(n*127);default:throw new Error("Invalid component type.")}}const E_={DEG2RAD:jo},Uf=class Uf{constructor(e=0,t=0){this.x=e,this.y=t}get width(){return this.x}set width(e){this.x=e}get height(){return this.y}set height(e){this.y=e}set(e,t){return this.x=e,this.y=t,this}setScalar(e){return this.x=e,this.y=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y)}copy(e){return this.x=e.x,this.y=e.y,this}add(e){return this.x+=e.x,this.y+=e.y,this}addScalar(e){return this.x+=e,this.y+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this}subScalar(e){return this.x-=e,this.y-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this}multiply(e){return this.x*=e.x,this.y*=e.y,this}multiplyScalar(e){return this.x*=e,this.y*=e,this}divide(e){return this.x/=e.x,this.y/=e.y,this}divideScalar(e){return this.multiplyScalar(1/e)}applyMatrix3(e){const t=this.x,r=this.y,i=e.elements;return this.x=i[0]*t+i[3]*r+i[6],this.y=i[1]*t+i[4]*r+i[7],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this}clamp(e,t){return this.x=at(this.x,e.x,t.x),this.y=at(this.y,e.y,t.y),this}clampScalar(e,t){return this.x=at(this.x,e,t),this.y=at(this.y,e,t),this}clampLength(e,t){const r=this.length();return this.divideScalar(r||1).multiplyScalar(at(r,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this}negate(){return this.x=-this.x,this.y=-this.y,this}dot(e){return this.x*e.x+this.y*e.y}cross(e){return this.x*e.y-this.y*e.x}lengthSq(){return this.x*this.x+this.y*this.y}length(){return Math.sqrt(this.x*this.x+this.y*this.y)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)}normalize(){return this.divideScalar(this.length()||1)}angle(){return Math.atan2(-this.y,-this.x)+Math.PI}angleTo(e){const t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;const r=this.dot(e)/t;return Math.acos(at(r,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){const t=this.x-e.x,r=this.y-e.y;return t*t+r*r}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this}lerpVectors(e,t,r){return this.x=e.x+(t.x-e.x)*r,this.y=e.y+(t.y-e.y)*r,this}equals(e){return e.x===this.x&&e.y===this.y}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this}rotateAround(e,t){const r=Math.cos(t),i=Math.sin(t),s=this.x-e.x,a=this.y-e.y;return this.x=s*r-a*i+e.x,this.y=s*i+a*r+e.y,this}random(){return this.x=Math.random(),this.y=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y}};Uf.prototype.isVector2=!0;let We=Uf;class vr{constructor(e=0,t=0,r=0,i=1){this.isQuaternion=!0,this._x=e,this._y=t,this._z=r,this._w=i}static slerpFlat(e,t,r,i,s,a,o){let l=r[i+0],c=r[i+1],u=r[i+2],f=r[i+3],h=s[a+0],d=s[a+1],m=s[a+2],g=s[a+3];if(f!==g||l!==h||c!==d||u!==m){let p=l*h+c*d+u*m+f*g;p<0&&(h=-h,d=-d,m=-m,g=-g,p=-p);let _=1-o;if(p<.9995){const M=Math.acos(p),y=Math.sin(M);_=Math.sin(_*M)/y,o=Math.sin(o*M)/y,l=l*_+h*o,c=c*_+d*o,u=u*_+m*o,f=f*_+g*o}else{l=l*_+h*o,c=c*_+d*o,u=u*_+m*o,f=f*_+g*o;const M=1/Math.sqrt(l*l+c*c+u*u+f*f);l*=M,c*=M,u*=M,f*=M}}e[t]=l,e[t+1]=c,e[t+2]=u,e[t+3]=f}static multiplyQuaternionsFlat(e,t,r,i,s,a){const o=r[i],l=r[i+1],c=r[i+2],u=r[i+3],f=s[a],h=s[a+1],d=s[a+2],m=s[a+3];return e[t]=o*m+u*f+l*d-c*h,e[t+1]=l*m+u*h+c*f-o*d,e[t+2]=c*m+u*d+o*h-l*f,e[t+3]=u*m-o*f-l*h-c*d,e}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get w(){return this._w}set w(e){this._w=e,this._onChangeCallback()}set(e,t,r,i){return this._x=e,this._y=t,this._z=r,this._w=i,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._w)}copy(e){return this._x=e.x,this._y=e.y,this._z=e.z,this._w=e.w,this._onChangeCallback(),this}setFromEuler(e,t=!0){const r=e._x,i=e._y,s=e._z,a=e._order,o=Math.cos,l=Math.sin,c=o(r/2),u=o(i/2),f=o(s/2),h=l(r/2),d=l(i/2),m=l(s/2);switch(a){case"XYZ":this._x=h*u*f+c*d*m,this._y=c*d*f-h*u*m,this._z=c*u*m+h*d*f,this._w=c*u*f-h*d*m;break;case"YXZ":this._x=h*u*f+c*d*m,this._y=c*d*f-h*u*m,this._z=c*u*m-h*d*f,this._w=c*u*f+h*d*m;break;case"ZXY":this._x=h*u*f-c*d*m,this._y=c*d*f+h*u*m,this._z=c*u*m+h*d*f,this._w=c*u*f-h*d*m;break;case"ZYX":this._x=h*u*f-c*d*m,this._y=c*d*f+h*u*m,this._z=c*u*m-h*d*f,this._w=c*u*f+h*d*m;break;case"YZX":this._x=h*u*f+c*d*m,this._y=c*d*f+h*u*m,this._z=c*u*m-h*d*f,this._w=c*u*f-h*d*m;break;case"XZY":this._x=h*u*f-c*d*m,this._y=c*d*f-h*u*m,this._z=c*u*m+h*d*f,this._w=c*u*f+h*d*m;break;default:$e("Quaternion: .setFromEuler() encountered an unknown order: "+a)}return t===!0&&this._onChangeCallback(),this}setFromAxisAngle(e,t){const r=t/2,i=Math.sin(r);return this._x=e.x*i,this._y=e.y*i,this._z=e.z*i,this._w=Math.cos(r),this._onChangeCallback(),this}setFromRotationMatrix(e){const t=e.elements,r=t[0],i=t[4],s=t[8],a=t[1],o=t[5],l=t[9],c=t[2],u=t[6],f=t[10],h=r+o+f;if(h>0){const d=.5/Math.sqrt(h+1);this._w=.25/d,this._x=(u-l)*d,this._y=(s-c)*d,this._z=(a-i)*d}else if(r>o&&r>f){const d=2*Math.sqrt(1+r-o-f);this._w=(u-l)/d,this._x=.25*d,this._y=(i+a)/d,this._z=(s+c)/d}else if(o>f){const d=2*Math.sqrt(1+o-r-f);this._w=(s-c)/d,this._x=(i+a)/d,this._y=.25*d,this._z=(l+u)/d}else{const d=2*Math.sqrt(1+f-r-o);this._w=(a-i)/d,this._x=(s+c)/d,this._y=(l+u)/d,this._z=.25*d}return this._onChangeCallback(),this}setFromUnitVectors(e,t){let r=e.dot(t)+1;return r<1e-8?(r=0,Math.abs(e.x)>Math.abs(e.z)?(this._x=-e.y,this._y=e.x,this._z=0,this._w=r):(this._x=0,this._y=-e.z,this._z=e.y,this._w=r)):(this._x=e.y*t.z-e.z*t.y,this._y=e.z*t.x-e.x*t.z,this._z=e.x*t.y-e.y*t.x,this._w=r),this.normalize()}angleTo(e){return 2*Math.acos(Math.abs(at(this.dot(e),-1,1)))}rotateTowards(e,t){const r=this.angleTo(e);if(r===0)return this;const i=Math.min(1,t/r);return this.slerp(e,i),this}identity(){return this.set(0,0,0,1)}invert(){return this.conjugate()}conjugate(){return this._x*=-1,this._y*=-1,this._z*=-1,this._onChangeCallback(),this}dot(e){return this._x*e._x+this._y*e._y+this._z*e._z+this._w*e._w}lengthSq(){return this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w}length(){return Math.sqrt(this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w)}normalize(){let e=this.length();return e===0?(this._x=0,this._y=0,this._z=0,this._w=1):(e=1/e,this._x=this._x*e,this._y=this._y*e,this._z=this._z*e,this._w=this._w*e),this._onChangeCallback(),this}multiply(e){return this.multiplyQuaternions(this,e)}premultiply(e){return this.multiplyQuaternions(e,this)}multiplyQuaternions(e,t){const r=e._x,i=e._y,s=e._z,a=e._w,o=t._x,l=t._y,c=t._z,u=t._w;return this._x=r*u+a*o+i*c-s*l,this._y=i*u+a*l+s*o-r*c,this._z=s*u+a*c+r*l-i*o,this._w=a*u-r*o-i*l-s*c,this._onChangeCallback(),this}slerp(e,t){let r=e._x,i=e._y,s=e._z,a=e._w,o=this.dot(e);o<0&&(r=-r,i=-i,s=-s,a=-a,o=-o);let l=1-t;if(o<.9995){const c=Math.acos(o),u=Math.sin(c);l=Math.sin(l*c)/u,t=Math.sin(t*c)/u,this._x=this._x*l+r*t,this._y=this._y*l+i*t,this._z=this._z*l+s*t,this._w=this._w*l+a*t,this._onChangeCallback()}else this._x=this._x*l+r*t,this._y=this._y*l+i*t,this._z=this._z*l+s*t,this._w=this._w*l+a*t,this.normalize();return this}slerpQuaternions(e,t,r){return this.copy(e).slerp(t,r)}random(){const e=2*Math.PI*Math.random(),t=2*Math.PI*Math.random(),r=Math.random(),i=Math.sqrt(1-r),s=Math.sqrt(r);return this.set(i*Math.sin(e),i*Math.cos(e),s*Math.sin(t),s*Math.cos(t))}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._w===this._w}fromArray(e,t=0){return this._x=e[t],this._y=e[t+1],this._z=e[t+2],this._w=e[t+3],this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._w,e}fromBufferAttribute(e,t){return this._x=e.getX(t),this._y=e.getY(t),this._z=e.getZ(t),this._w=e.getW(t),this._onChangeCallback(),this}toJSON(){return this.toArray()}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._w}}const Lf=class Lf{constructor(e=0,t=0,r=0){this.x=e,this.y=t,this.z=r}set(e,t,r){return r===void 0&&(r=this.z),this.x=e,this.y=t,this.z=r,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this}multiplyVectors(e,t){return this.x=e.x*t.x,this.y=e.y*t.y,this.z=e.z*t.z,this}applyEuler(e){return this.applyQuaternion(td.setFromEuler(e))}applyAxisAngle(e,t){return this.applyQuaternion(td.setFromAxisAngle(e,t))}applyMatrix3(e){const t=this.x,r=this.y,i=this.z,s=e.elements;return this.x=s[0]*t+s[3]*r+s[6]*i,this.y=s[1]*t+s[4]*r+s[7]*i,this.z=s[2]*t+s[5]*r+s[8]*i,this}applyNormalMatrix(e){return this.applyMatrix3(e).normalize()}applyMatrix4(e){const t=this.x,r=this.y,i=this.z,s=e.elements,a=1/(s[3]*t+s[7]*r+s[11]*i+s[15]);return this.x=(s[0]*t+s[4]*r+s[8]*i+s[12])*a,this.y=(s[1]*t+s[5]*r+s[9]*i+s[13])*a,this.z=(s[2]*t+s[6]*r+s[10]*i+s[14])*a,this}applyQuaternion(e){const t=this.x,r=this.y,i=this.z,s=e.x,a=e.y,o=e.z,l=e.w,c=2*(a*i-o*r),u=2*(o*t-s*i),f=2*(s*r-a*t);return this.x=t+l*c+a*f-o*u,this.y=r+l*u+o*c-s*f,this.z=i+l*f+s*u-a*c,this}project(e){return this.applyMatrix4(e.matrixWorldInverse).applyMatrix4(e.projectionMatrix)}unproject(e){return this.applyMatrix4(e.projectionMatrixInverse).applyMatrix4(e.matrixWorld)}transformDirection(e){const t=this.x,r=this.y,i=this.z,s=e.elements;return this.x=s[0]*t+s[4]*r+s[8]*i,this.y=s[1]*t+s[5]*r+s[9]*i,this.z=s[2]*t+s[6]*r+s[10]*i,this.normalize()}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this}divideScalar(e){return this.multiplyScalar(1/e)}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this}clamp(e,t){return this.x=at(this.x,e.x,t.x),this.y=at(this.y,e.y,t.y),this.z=at(this.z,e.z,t.z),this}clampScalar(e,t){return this.x=at(this.x,e,t),this.y=at(this.y,e,t),this.z=at(this.z,e,t),this}clampLength(e,t){const r=this.length();return this.divideScalar(r||1).multiplyScalar(at(r,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this}lerpVectors(e,t,r){return this.x=e.x+(t.x-e.x)*r,this.y=e.y+(t.y-e.y)*r,this.z=e.z+(t.z-e.z)*r,this}cross(e){return this.crossVectors(this,e)}crossVectors(e,t){const r=e.x,i=e.y,s=e.z,a=t.x,o=t.y,l=t.z;return this.x=i*l-s*o,this.y=s*a-r*l,this.z=r*o-i*a,this}projectOnVector(e){const t=e.lengthSq();if(t===0)return this.set(0,0,0);const r=e.dot(this)/t;return this.copy(e).multiplyScalar(r)}projectOnPlane(e){return sc.copy(this).projectOnVector(e),this.sub(sc)}reflect(e){return this.sub(sc.copy(e).multiplyScalar(2*this.dot(e)))}angleTo(e){const t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;const r=this.dot(e)/t;return Math.acos(at(r,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){const t=this.x-e.x,r=this.y-e.y,i=this.z-e.z;return t*t+r*r+i*i}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)+Math.abs(this.z-e.z)}setFromSpherical(e){return this.setFromSphericalCoords(e.radius,e.phi,e.theta)}setFromSphericalCoords(e,t,r){const i=Math.sin(t)*e;return this.x=i*Math.sin(r),this.y=Math.cos(t)*e,this.z=i*Math.cos(r),this}setFromCylindrical(e){return this.setFromCylindricalCoords(e.radius,e.theta,e.y)}setFromCylindricalCoords(e,t,r){return this.x=e*Math.sin(t),this.y=r,this.z=e*Math.cos(t),this}setFromMatrixPosition(e){const t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this}setFromMatrixScale(e){const t=this.setFromMatrixColumn(e,0).length(),r=this.setFromMatrixColumn(e,1).length(),i=this.setFromMatrixColumn(e,2).length();return this.x=t,this.y=r,this.z=i,this}setFromMatrixColumn(e,t){return this.fromArray(e.elements,t*4)}setFromMatrix3Column(e,t){return this.fromArray(e.elements,t*3)}setFromEuler(e){return this.x=e._x,this.y=e._y,this.z=e._z,this}setFromColor(e){return this.x=e.r,this.y=e.g,this.z=e.b,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this}randomDirection(){const e=Math.random()*Math.PI*2,t=Math.random()*2-1,r=Math.sqrt(1-t*t);return this.x=r*Math.cos(e),this.y=t,this.z=r*Math.sin(e),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z}};Lf.prototype.isVector3=!0;let X=Lf;const sc=new X,td=new vr,If=class If{constructor(e,t,r,i,s,a,o,l,c){this.elements=[1,0,0,0,1,0,0,0,1],e!==void 0&&this.set(e,t,r,i,s,a,o,l,c)}set(e,t,r,i,s,a,o,l,c){const u=this.elements;return u[0]=e,u[1]=i,u[2]=o,u[3]=t,u[4]=s,u[5]=l,u[6]=r,u[7]=a,u[8]=c,this}identity(){return this.set(1,0,0,0,1,0,0,0,1),this}copy(e){const t=this.elements,r=e.elements;return t[0]=r[0],t[1]=r[1],t[2]=r[2],t[3]=r[3],t[4]=r[4],t[5]=r[5],t[6]=r[6],t[7]=r[7],t[8]=r[8],this}extractBasis(e,t,r){return e.setFromMatrix3Column(this,0),t.setFromMatrix3Column(this,1),r.setFromMatrix3Column(this,2),this}setFromMatrix4(e){const t=e.elements;return this.set(t[0],t[4],t[8],t[1],t[5],t[9],t[2],t[6],t[10]),this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){const r=e.elements,i=t.elements,s=this.elements,a=r[0],o=r[3],l=r[6],c=r[1],u=r[4],f=r[7],h=r[2],d=r[5],m=r[8],g=i[0],p=i[3],_=i[6],M=i[1],y=i[4],v=i[7],S=i[2],b=i[5],E=i[8];return s[0]=a*g+o*M+l*S,s[3]=a*p+o*y+l*b,s[6]=a*_+o*v+l*E,s[1]=c*g+u*M+f*S,s[4]=c*p+u*y+f*b,s[7]=c*_+u*v+f*E,s[2]=h*g+d*M+m*S,s[5]=h*p+d*y+m*b,s[8]=h*_+d*v+m*E,this}multiplyScalar(e){const t=this.elements;return t[0]*=e,t[3]*=e,t[6]*=e,t[1]*=e,t[4]*=e,t[7]*=e,t[2]*=e,t[5]*=e,t[8]*=e,this}determinant(){const e=this.elements,t=e[0],r=e[1],i=e[2],s=e[3],a=e[4],o=e[5],l=e[6],c=e[7],u=e[8];return t*a*u-t*o*c-r*s*u+r*o*l+i*s*c-i*a*l}invert(){const e=this.elements,t=e[0],r=e[1],i=e[2],s=e[3],a=e[4],o=e[5],l=e[6],c=e[7],u=e[8],f=u*a-o*c,h=o*l-u*s,d=c*s-a*l,m=t*f+r*h+i*d;if(m===0)return this.set(0,0,0,0,0,0,0,0,0);const g=1/m;return e[0]=f*g,e[1]=(i*c-u*r)*g,e[2]=(o*r-i*a)*g,e[3]=h*g,e[4]=(u*t-i*l)*g,e[5]=(i*s-o*t)*g,e[6]=d*g,e[7]=(r*l-c*t)*g,e[8]=(a*t-r*s)*g,this}transpose(){let e;const t=this.elements;return e=t[1],t[1]=t[3],t[3]=e,e=t[2],t[2]=t[6],t[6]=e,e=t[5],t[5]=t[7],t[7]=e,this}getNormalMatrix(e){return this.setFromMatrix4(e).invert().transpose()}transposeIntoArray(e){const t=this.elements;return e[0]=t[0],e[1]=t[3],e[2]=t[6],e[3]=t[1],e[4]=t[4],e[5]=t[7],e[6]=t[2],e[7]=t[5],e[8]=t[8],this}setUvTransform(e,t,r,i,s,a,o){const l=Math.cos(s),c=Math.sin(s);return this.set(r*l,r*c,-r*(l*a+c*o)+a+e,-i*c,i*l,-i*(-c*a+l*o)+o+t,0,0,1),this}scale(e,t){return this.premultiply(ac.makeScale(e,t)),this}rotate(e){return this.premultiply(ac.makeRotation(-e)),this}translate(e,t){return this.premultiply(ac.makeTranslation(e,t)),this}makeTranslation(e,t){return e.isVector2?this.set(1,0,e.x,0,1,e.y,0,0,1):this.set(1,0,e,0,1,t,0,0,1),this}makeRotation(e){const t=Math.cos(e),r=Math.sin(e);return this.set(t,-r,0,r,t,0,0,0,1),this}makeScale(e,t){return this.set(e,0,0,0,t,0,0,0,1),this}equals(e){const t=this.elements,r=e.elements;for(let i=0;i<9;i++)if(t[i]!==r[i])return!1;return!0}fromArray(e,t=0){for(let r=0;r<9;r++)this.elements[r]=e[r+t];return this}toArray(e=[],t=0){const r=this.elements;return e[t]=r[0],e[t+1]=r[1],e[t+2]=r[2],e[t+3]=r[3],e[t+4]=r[4],e[t+5]=r[5],e[t+6]=r[6],e[t+7]=r[7],e[t+8]=r[8],e}clone(){return new this.constructor().fromArray(this.elements)}};If.prototype.isMatrix3=!0;let nt=If;const ac=new nt,nd=new nt().set(.4123908,.3575843,.1804808,.212639,.7151687,.0721923,.0193308,.1191948,.9505322),id=new nt().set(3.2409699,-1.5373832,-.4986108,-.9692436,1.8759675,.0415551,.0556301,-.203977,1.0569715);function w_(){const n={enabled:!0,workingColorSpace:ks,spaces:{},convert:function(i,s,a){return this.enabled===!1||s===a||!s||!a||(this.spaces[s].transfer===xt&&(i.r=Vi(i.r),i.g=Vi(i.g),i.b=Vi(i.b)),this.spaces[s].primaries!==this.spaces[a].primaries&&(i.applyMatrix3(this.spaces[s].toXYZ),i.applyMatrix3(this.spaces[a].fromXYZ)),this.spaces[a].transfer===xt&&(i.r=Ds(i.r),i.g=Ds(i.g),i.b=Ds(i.b))),i},workingToColorSpace:function(i,s){return this.convert(i,this.workingColorSpace,s)},colorSpaceToWorking:function(i,s){return this.convert(i,s,this.workingColorSpace)},getPrimaries:function(i){return this.spaces[i].primaries},getTransfer:function(i){return i===yi?al:this.spaces[i].transfer},getToneMappingMode:function(i){return this.spaces[i].outputColorSpaceConfig.toneMappingMode||"standard"},getLuminanceCoefficients:function(i,s=this.workingColorSpace){return i.fromArray(this.spaces[s].luminanceCoefficients)},define:function(i){Object.assign(this.spaces,i)},_getMatrix:function(i,s,a){return i.copy(this.spaces[s].toXYZ).multiply(this.spaces[a].fromXYZ)},_getDrawingBufferColorSpace:function(i){return this.spaces[i].outputColorSpaceConfig.drawingBufferColorSpace},_getUnpackColorSpace:function(i=this.workingColorSpace){return this.spaces[i].workingColorSpaceConfig.unpackColorSpace},fromWorkingColorSpace:function(i,s){return lh("ColorManagement: .fromWorkingColorSpace() has been renamed to .workingToColorSpace()."),n.workingToColorSpace(i,s)},toWorkingColorSpace:function(i,s){return lh("ColorManagement: .toWorkingColorSpace() has been renamed to .colorSpaceToWorking()."),n.colorSpaceToWorking(i,s)}},e=[.64,.33,.3,.6,.15,.06],t=[.2126,.7152,.0722],r=[.3127,.329];return n.define({[ks]:{primaries:e,whitePoint:r,transfer:al,toXYZ:nd,fromXYZ:id,luminanceCoefficients:t,workingColorSpaceConfig:{unpackColorSpace:bt},outputColorSpaceConfig:{drawingBufferColorSpace:bt}},[bt]:{primaries:e,whitePoint:r,transfer:xt,toXYZ:nd,fromXYZ:id,luminanceCoefficients:t,outputColorSpaceConfig:{drawingBufferColorSpace:bt}}}),n}const ut=w_();function Vi(n){return n<.04045?n*.0773993808:Math.pow(n*.9478672986+.0521327014,2.4)}function Ds(n){return n<.0031308?n*12.92:1.055*Math.pow(n,.41666)-.055}let os;class A_{static getDataURL(e,t="image/png"){if(/^data:/i.test(e.src)||typeof HTMLCanvasElement>"u")return e.src;let r;if(e instanceof HTMLCanvasElement)r=e;else{os===void 0&&(os=ll("canvas")),os.width=e.width,os.height=e.height;const i=os.getContext("2d");e instanceof ImageData?i.putImageData(e,0,0):i.drawImage(e,0,0,e.width,e.height),r=os}return r.toDataURL(t)}static sRGBToLinear(e){if(typeof HTMLImageElement<"u"&&e instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&e instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&e instanceof ImageBitmap){const t=ll("canvas");t.width=e.width,t.height=e.height;const r=t.getContext("2d");r.drawImage(e,0,0,e.width,e.height);const i=r.getImageData(0,0,e.width,e.height),s=i.data;for(let a=0;a<s.length;a++)s[a]=Vi(s[a]/255)*255;return r.putImageData(i,0,0),t}else if(e.data){const t=e.data.slice(0);for(let r=0;r<t.length;r++)t instanceof Uint8Array||t instanceof Uint8ClampedArray?t[r]=Math.floor(Vi(t[r]/255)*255):t[r]=Vi(t[r]);return{data:t,width:e.width,height:e.height}}else return $e("ImageUtils.sRGBToLinear(): Unsupported image type. No color space conversion applied."),e}}let R_=0;class Zh{constructor(e=null){this.isSource=!0,Object.defineProperty(this,"id",{value:R_++}),this.uuid=pr(),this.data=e,this.dataReady=!0,this.version=0}getSize(e){const t=this.data;return typeof HTMLVideoElement<"u"&&t instanceof HTMLVideoElement?e.set(t.videoWidth,t.videoHeight,0):typeof VideoFrame<"u"&&t instanceof VideoFrame?e.set(t.displayWidth,t.displayHeight,0):t!==null?e.set(t.width,t.height,t.depth||0):e.set(0,0,0),e}set needsUpdate(e){e===!0&&this.version++}toJSON(e){const t=e===void 0||typeof e=="string";if(!t&&e.images[this.uuid]!==void 0)return e.images[this.uuid];const r={uuid:this.uuid,url:""},i=this.data;if(i!==null){let s;if(Array.isArray(i)){s=[];for(let a=0,o=i.length;a<o;a++)i[a].isDataTexture?s.push(oc(i[a].image)):s.push(oc(i[a]))}else s=oc(i);r.url=s}return t||(e.images[this.uuid]=r),r}}function oc(n){return typeof HTMLImageElement<"u"&&n instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&n instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&n instanceof ImageBitmap?A_.getDataURL(n):n.data?{data:Array.from(n.data),width:n.width,height:n.height,type:n.data.constructor.name}:($e("Texture: Unable to serialize Texture."),{})}let C_=0;const lc=new X;class Zt extends hi{constructor(e=Zt.DEFAULT_IMAGE,t=Zt.DEFAULT_MAPPING,r=Hi,i=Hi,s=zt,a=Br,o=ci,l=Yt,c=Zt.DEFAULT_ANISOTROPY,u=yi){super(),this.isTexture=!0,Object.defineProperty(this,"id",{value:C_++}),this.uuid=pr(),this.name="",this.source=new Zh(e),this.mipmaps=[],this.mapping=t,this.channel=0,this.wrapS=r,this.wrapT=i,this.magFilter=s,this.minFilter=a,this.anisotropy=c,this.format=o,this.internalFormat=null,this.type=l,this.offset=new We(0,0),this.repeat=new We(1,1),this.center=new We(0,0),this.rotation=0,this.matrixAutoUpdate=!0,this.matrix=new nt,this.generateMipmaps=!0,this.premultiplyAlpha=!1,this.flipY=!0,this.unpackAlignment=4,this.colorSpace=u,this.userData={},this.updateRanges=[],this.version=0,this.onUpdate=null,this.renderTarget=null,this.isRenderTargetTexture=!1,this.isArrayTexture=!!(e&&e.depth&&e.depth>1),this.pmremVersion=0,this.normalized=!1}get width(){return this.source.getSize(lc).x}get height(){return this.source.getSize(lc).y}get depth(){return this.source.getSize(lc).z}get image(){return this.source.data}set image(e){this.source.data=e}updateMatrix(){this.matrix.setUvTransform(this.offset.x,this.offset.y,this.repeat.x,this.repeat.y,this.rotation,this.center.x,this.center.y)}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}clone(){return new this.constructor().copy(this)}copy(e){return this.name=e.name,this.source=e.source,this.mipmaps=e.mipmaps.slice(0),this.mapping=e.mapping,this.channel=e.channel,this.wrapS=e.wrapS,this.wrapT=e.wrapT,this.magFilter=e.magFilter,this.minFilter=e.minFilter,this.anisotropy=e.anisotropy,this.format=e.format,this.internalFormat=e.internalFormat,this.type=e.type,this.normalized=e.normalized,this.offset.copy(e.offset),this.repeat.copy(e.repeat),this.center.copy(e.center),this.rotation=e.rotation,this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrix.copy(e.matrix),this.generateMipmaps=e.generateMipmaps,this.premultiplyAlpha=e.premultiplyAlpha,this.flipY=e.flipY,this.unpackAlignment=e.unpackAlignment,this.colorSpace=e.colorSpace,this.renderTarget=e.renderTarget,this.isRenderTargetTexture=e.isRenderTargetTexture,this.isArrayTexture=e.isArrayTexture,this.userData=JSON.parse(JSON.stringify(e.userData)),this.needsUpdate=!0,this}setValues(e){for(const t in e){const r=e[t];if(r===void 0){$e(`Texture.setValues(): parameter '${t}' has value of undefined.`);continue}const i=this[t];if(i===void 0){$e(`Texture.setValues(): property '${t}' does not exist.`);continue}i&&r&&i.isVector2&&r.isVector2||i&&r&&i.isVector3&&r.isVector3||i&&r&&i.isMatrix3&&r.isMatrix3?i.copy(r):this[t]=r}}toJSON(e){const t=e===void 0||typeof e=="string";if(!t&&e.textures[this.uuid]!==void 0)return e.textures[this.uuid];const r={metadata:{version:4.7,type:"Texture",generator:"Texture.toJSON"},uuid:this.uuid,name:this.name,image:this.source.toJSON(e).uuid,mapping:this.mapping,channel:this.channel,repeat:[this.repeat.x,this.repeat.y],offset:[this.offset.x,this.offset.y],center:[this.center.x,this.center.y],rotation:this.rotation,wrap:[this.wrapS,this.wrapT],format:this.format,internalFormat:this.internalFormat,type:this.type,normalized:this.normalized,colorSpace:this.colorSpace,minFilter:this.minFilter,magFilter:this.magFilter,anisotropy:this.anisotropy,flipY:this.flipY,generateMipmaps:this.generateMipmaps,premultiplyAlpha:this.premultiplyAlpha,unpackAlignment:this.unpackAlignment};return Object.keys(this.userData).length>0&&(r.userData=this.userData),t||(e.textures[this.uuid]=r),r}dispose(){this.dispatchEvent({type:"dispose"})}transformUv(e){if(this.mapping!==vm)return e;if(e.applyMatrix3(this.matrix),e.x<0||e.x>1)switch(this.wrapS){case Cu:e.x=e.x-Math.floor(e.x);break;case Hi:e.x=e.x<0?0:1;break;case Pu:Math.abs(Math.floor(e.x)%2)===1?e.x=Math.ceil(e.x)-e.x:e.x=e.x-Math.floor(e.x);break}if(e.y<0||e.y>1)switch(this.wrapT){case Cu:e.y=e.y-Math.floor(e.y);break;case Hi:e.y=e.y<0?0:1;break;case Pu:Math.abs(Math.floor(e.y)%2)===1?e.y=Math.ceil(e.y)-e.y:e.y=e.y-Math.floor(e.y);break}return this.flipY&&(e.y=1-e.y),e}set needsUpdate(e){e===!0&&(this.version++,this.source.needsUpdate=!0)}set needsPMREMUpdate(e){e===!0&&this.pmremVersion++}}Zt.DEFAULT_IMAGE=null;Zt.DEFAULT_MAPPING=vm;Zt.DEFAULT_ANISOTROPY=1;const Ff=class Ff{constructor(e=0,t=0,r=0,i=1){this.x=e,this.y=t,this.z=r,this.w=i}get width(){return this.z}set width(e){this.z=e}get height(){return this.w}set height(e){this.w=e}set(e,t,r,i){return this.x=e,this.y=t,this.z=r,this.w=i,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this.w=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setW(e){return this.w=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;case 3:this.w=t;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;case 3:return this.w;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z,this.w)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this.w=e.w!==void 0?e.w:1,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this.w+=e.w,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this.w+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this.w=e.w+t.w,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this.w+=e.w*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this.w-=e.w,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this.w-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this.w=e.w-t.w,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this.w*=e.w,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this.w*=e,this}applyMatrix4(e){const t=this.x,r=this.y,i=this.z,s=this.w,a=e.elements;return this.x=a[0]*t+a[4]*r+a[8]*i+a[12]*s,this.y=a[1]*t+a[5]*r+a[9]*i+a[13]*s,this.z=a[2]*t+a[6]*r+a[10]*i+a[14]*s,this.w=a[3]*t+a[7]*r+a[11]*i+a[15]*s,this}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this.w/=e.w,this}divideScalar(e){return this.multiplyScalar(1/e)}setAxisAngleFromQuaternion(e){this.w=2*Math.acos(e.w);const t=Math.sqrt(1-e.w*e.w);return t<1e-4?(this.x=1,this.y=0,this.z=0):(this.x=e.x/t,this.y=e.y/t,this.z=e.z/t),this}setAxisAngleFromRotationMatrix(e){let t,r,i,s;const l=e.elements,c=l[0],u=l[4],f=l[8],h=l[1],d=l[5],m=l[9],g=l[2],p=l[6],_=l[10];if(Math.abs(u-h)<.01&&Math.abs(f-g)<.01&&Math.abs(m-p)<.01){if(Math.abs(u+h)<.1&&Math.abs(f+g)<.1&&Math.abs(m+p)<.1&&Math.abs(c+d+_-3)<.1)return this.set(1,0,0,0),this;t=Math.PI;const y=(c+1)/2,v=(d+1)/2,S=(_+1)/2,b=(u+h)/4,E=(f+g)/4,x=(m+p)/4;return y>v&&y>S?y<.01?(r=0,i=.707106781,s=.707106781):(r=Math.sqrt(y),i=b/r,s=E/r):v>S?v<.01?(r=.707106781,i=0,s=.707106781):(i=Math.sqrt(v),r=b/i,s=x/i):S<.01?(r=.707106781,i=.707106781,s=0):(s=Math.sqrt(S),r=E/s,i=x/s),this.set(r,i,s,t),this}let M=Math.sqrt((p-m)*(p-m)+(f-g)*(f-g)+(h-u)*(h-u));return Math.abs(M)<.001&&(M=1),this.x=(p-m)/M,this.y=(f-g)/M,this.z=(h-u)/M,this.w=Math.acos((c+d+_-1)/2),this}setFromMatrixPosition(e){const t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this.w=t[15],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this.w=Math.min(this.w,e.w),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this.w=Math.max(this.w,e.w),this}clamp(e,t){return this.x=at(this.x,e.x,t.x),this.y=at(this.y,e.y,t.y),this.z=at(this.z,e.z,t.z),this.w=at(this.w,e.w,t.w),this}clampScalar(e,t){return this.x=at(this.x,e,t),this.y=at(this.y,e,t),this.z=at(this.z,e,t),this.w=at(this.w,e,t),this}clampLength(e,t){const r=this.length();return this.divideScalar(r||1).multiplyScalar(at(r,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this.w=Math.floor(this.w),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this.w=Math.ceil(this.w),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this.w=Math.round(this.w),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this.w=Math.trunc(this.w),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this.w=-this.w,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z+this.w*e.w}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)+Math.abs(this.w)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this.w+=(e.w-this.w)*t,this}lerpVectors(e,t,r){return this.x=e.x+(t.x-e.x)*r,this.y=e.y+(t.y-e.y)*r,this.z=e.z+(t.z-e.z)*r,this.w=e.w+(t.w-e.w)*r,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z&&e.w===this.w}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this.w=e[t+3],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e[t+3]=this.w,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this.w=e.getW(t),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this.w=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z,yield this.w}};Ff.prototype.isVector4=!0;let Ct=Ff;class P_ extends hi{constructor(e=1,t=1,r={}){super(),r=Object.assign({generateMipmaps:!1,internalFormat:null,minFilter:zt,depthBuffer:!0,stencilBuffer:!1,resolveDepthBuffer:!0,resolveStencilBuffer:!0,depthTexture:null,samples:0,count:1,depth:1,multiview:!1},r),this.isRenderTarget=!0,this.width=e,this.height=t,this.depth=r.depth,this.scissor=new Ct(0,0,e,t),this.scissorTest=!1,this.viewport=new Ct(0,0,e,t),this.textures=[];const i={width:e,height:t,depth:r.depth},s=new Zt(i),a=r.count;for(let o=0;o<a;o++)this.textures[o]=s.clone(),this.textures[o].isRenderTargetTexture=!0,this.textures[o].renderTarget=this;this._setTextureOptions(r),this.depthBuffer=r.depthBuffer,this.stencilBuffer=r.stencilBuffer,this.resolveDepthBuffer=r.resolveDepthBuffer,this.resolveStencilBuffer=r.resolveStencilBuffer,this._depthTexture=null,this.depthTexture=r.depthTexture,this.samples=r.samples,this.multiview=r.multiview}_setTextureOptions(e={}){const t={minFilter:zt,generateMipmaps:!1,flipY:!1,internalFormat:null};e.mapping!==void 0&&(t.mapping=e.mapping),e.wrapS!==void 0&&(t.wrapS=e.wrapS),e.wrapT!==void 0&&(t.wrapT=e.wrapT),e.wrapR!==void 0&&(t.wrapR=e.wrapR),e.magFilter!==void 0&&(t.magFilter=e.magFilter),e.minFilter!==void 0&&(t.minFilter=e.minFilter),e.format!==void 0&&(t.format=e.format),e.type!==void 0&&(t.type=e.type),e.anisotropy!==void 0&&(t.anisotropy=e.anisotropy),e.colorSpace!==void 0&&(t.colorSpace=e.colorSpace),e.flipY!==void 0&&(t.flipY=e.flipY),e.generateMipmaps!==void 0&&(t.generateMipmaps=e.generateMipmaps),e.internalFormat!==void 0&&(t.internalFormat=e.internalFormat);for(let r=0;r<this.textures.length;r++)this.textures[r].setValues(t)}get texture(){return this.textures[0]}set texture(e){this.textures[0]=e}set depthTexture(e){this._depthTexture!==null&&(this._depthTexture.renderTarget=null),e!==null&&(e.renderTarget=this),this._depthTexture=e}get depthTexture(){return this._depthTexture}setSize(e,t,r=1){if(this.width!==e||this.height!==t||this.depth!==r){this.width=e,this.height=t,this.depth=r;for(let i=0,s=this.textures.length;i<s;i++)this.textures[i].image.width=e,this.textures[i].image.height=t,this.textures[i].image.depth=r,this.textures[i].isData3DTexture!==!0&&(this.textures[i].isArrayTexture=this.textures[i].image.depth>1);this.dispose()}this.viewport.set(0,0,e,t),this.scissor.set(0,0,e,t)}clone(){return new this.constructor().copy(this)}copy(e){this.width=e.width,this.height=e.height,this.depth=e.depth,this.scissor.copy(e.scissor),this.scissorTest=e.scissorTest,this.viewport.copy(e.viewport),this.textures.length=0;for(let t=0,r=e.textures.length;t<r;t++){this.textures[t]=e.textures[t].clone(),this.textures[t].isRenderTargetTexture=!0,this.textures[t].renderTarget=this;const i=Object.assign({},e.textures[t].image);this.textures[t].source=new Zh(i)}return this.depthBuffer=e.depthBuffer,this.stencilBuffer=e.stencilBuffer,this.resolveDepthBuffer=e.resolveDepthBuffer,this.resolveStencilBuffer=e.resolveStencilBuffer,e.depthTexture!==null&&(this.depthTexture=e.depthTexture.clone()),this.samples=e.samples,this.multiview=e.multiview,this}dispose(){this.dispatchEvent({type:"dispose"})}}class $t extends P_{constructor(e=1,t=1,r={}){super(e,t,r),this.isWebGLRenderTarget=!0}}class Am extends Zt{constructor(e=null,t=1,r=1,i=1){super(null),this.isDataArrayTexture=!0,this.image={data:e,width:t,height:r,depth:i},this.magFilter=cn,this.minFilter=cn,this.wrapR=Hi,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1,this.layerUpdates=new Set}addLayerUpdate(e){this.layerUpdates.add(e)}clearLayerUpdates(){this.layerUpdates.clear()}}class D_ extends Zt{constructor(e=null,t=1,r=1,i=1){super(null),this.isData3DTexture=!0,this.image={data:e,width:t,height:r,depth:i},this.magFilter=cn,this.minFilter=cn,this.wrapR=Hi,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}}const wl=class wl{constructor(e,t,r,i,s,a,o,l,c,u,f,h,d,m,g,p){this.elements=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],e!==void 0&&this.set(e,t,r,i,s,a,o,l,c,u,f,h,d,m,g,p)}set(e,t,r,i,s,a,o,l,c,u,f,h,d,m,g,p){const _=this.elements;return _[0]=e,_[4]=t,_[8]=r,_[12]=i,_[1]=s,_[5]=a,_[9]=o,_[13]=l,_[2]=c,_[6]=u,_[10]=f,_[14]=h,_[3]=d,_[7]=m,_[11]=g,_[15]=p,this}identity(){return this.set(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1),this}clone(){return new wl().fromArray(this.elements)}copy(e){const t=this.elements,r=e.elements;return t[0]=r[0],t[1]=r[1],t[2]=r[2],t[3]=r[3],t[4]=r[4],t[5]=r[5],t[6]=r[6],t[7]=r[7],t[8]=r[8],t[9]=r[9],t[10]=r[10],t[11]=r[11],t[12]=r[12],t[13]=r[13],t[14]=r[14],t[15]=r[15],this}copyPosition(e){const t=this.elements,r=e.elements;return t[12]=r[12],t[13]=r[13],t[14]=r[14],this}setFromMatrix3(e){const t=e.elements;return this.set(t[0],t[3],t[6],0,t[1],t[4],t[7],0,t[2],t[5],t[8],0,0,0,0,1),this}extractBasis(e,t,r){return this.determinant()===0?(e.set(1,0,0),t.set(0,1,0),r.set(0,0,1),this):(e.setFromMatrixColumn(this,0),t.setFromMatrixColumn(this,1),r.setFromMatrixColumn(this,2),this)}makeBasis(e,t,r){return this.set(e.x,t.x,r.x,0,e.y,t.y,r.y,0,e.z,t.z,r.z,0,0,0,0,1),this}extractRotation(e){if(e.determinant()===0)return this.identity();const t=this.elements,r=e.elements,i=1/ls.setFromMatrixColumn(e,0).length(),s=1/ls.setFromMatrixColumn(e,1).length(),a=1/ls.setFromMatrixColumn(e,2).length();return t[0]=r[0]*i,t[1]=r[1]*i,t[2]=r[2]*i,t[3]=0,t[4]=r[4]*s,t[5]=r[5]*s,t[6]=r[6]*s,t[7]=0,t[8]=r[8]*a,t[9]=r[9]*a,t[10]=r[10]*a,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromEuler(e){const t=this.elements,r=e.x,i=e.y,s=e.z,a=Math.cos(r),o=Math.sin(r),l=Math.cos(i),c=Math.sin(i),u=Math.cos(s),f=Math.sin(s);if(e.order==="XYZ"){const h=a*u,d=a*f,m=o*u,g=o*f;t[0]=l*u,t[4]=-l*f,t[8]=c,t[1]=d+m*c,t[5]=h-g*c,t[9]=-o*l,t[2]=g-h*c,t[6]=m+d*c,t[10]=a*l}else if(e.order==="YXZ"){const h=l*u,d=l*f,m=c*u,g=c*f;t[0]=h+g*o,t[4]=m*o-d,t[8]=a*c,t[1]=a*f,t[5]=a*u,t[9]=-o,t[2]=d*o-m,t[6]=g+h*o,t[10]=a*l}else if(e.order==="ZXY"){const h=l*u,d=l*f,m=c*u,g=c*f;t[0]=h-g*o,t[4]=-a*f,t[8]=m+d*o,t[1]=d+m*o,t[5]=a*u,t[9]=g-h*o,t[2]=-a*c,t[6]=o,t[10]=a*l}else if(e.order==="ZYX"){const h=a*u,d=a*f,m=o*u,g=o*f;t[0]=l*u,t[4]=m*c-d,t[8]=h*c+g,t[1]=l*f,t[5]=g*c+h,t[9]=d*c-m,t[2]=-c,t[6]=o*l,t[10]=a*l}else if(e.order==="YZX"){const h=a*l,d=a*c,m=o*l,g=o*c;t[0]=l*u,t[4]=g-h*f,t[8]=m*f+d,t[1]=f,t[5]=a*u,t[9]=-o*u,t[2]=-c*u,t[6]=d*f+m,t[10]=h-g*f}else if(e.order==="XZY"){const h=a*l,d=a*c,m=o*l,g=o*c;t[0]=l*u,t[4]=-f,t[8]=c*u,t[1]=h*f+g,t[5]=a*u,t[9]=d*f-m,t[2]=m*f-d,t[6]=o*u,t[10]=g*f+h}return t[3]=0,t[7]=0,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromQuaternion(e){return this.compose(U_,e,L_)}lookAt(e,t,r){const i=this.elements;return Nn.subVectors(e,t),Nn.lengthSq()===0&&(Nn.z=1),Nn.normalize(),tr.crossVectors(r,Nn),tr.lengthSq()===0&&(Math.abs(r.z)===1?Nn.x+=1e-4:Nn.z+=1e-4,Nn.normalize(),tr.crossVectors(r,Nn)),tr.normalize(),ao.crossVectors(Nn,tr),i[0]=tr.x,i[4]=ao.x,i[8]=Nn.x,i[1]=tr.y,i[5]=ao.y,i[9]=Nn.y,i[2]=tr.z,i[6]=ao.z,i[10]=Nn.z,this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){const r=e.elements,i=t.elements,s=this.elements,a=r[0],o=r[4],l=r[8],c=r[12],u=r[1],f=r[5],h=r[9],d=r[13],m=r[2],g=r[6],p=r[10],_=r[14],M=r[3],y=r[7],v=r[11],S=r[15],b=i[0],E=i[4],x=i[8],w=i[12],R=i[1],L=i[5],A=i[9],U=i[13],P=i[2],I=i[6],F=i[10],O=i[14],q=i[3],z=i[7],k=i[11],N=i[15];return s[0]=a*b+o*R+l*P+c*q,s[4]=a*E+o*L+l*I+c*z,s[8]=a*x+o*A+l*F+c*k,s[12]=a*w+o*U+l*O+c*N,s[1]=u*b+f*R+h*P+d*q,s[5]=u*E+f*L+h*I+d*z,s[9]=u*x+f*A+h*F+d*k,s[13]=u*w+f*U+h*O+d*N,s[2]=m*b+g*R+p*P+_*q,s[6]=m*E+g*L+p*I+_*z,s[10]=m*x+g*A+p*F+_*k,s[14]=m*w+g*U+p*O+_*N,s[3]=M*b+y*R+v*P+S*q,s[7]=M*E+y*L+v*I+S*z,s[11]=M*x+y*A+v*F+S*k,s[15]=M*w+y*U+v*O+S*N,this}multiplyScalar(e){const t=this.elements;return t[0]*=e,t[4]*=e,t[8]*=e,t[12]*=e,t[1]*=e,t[5]*=e,t[9]*=e,t[13]*=e,t[2]*=e,t[6]*=e,t[10]*=e,t[14]*=e,t[3]*=e,t[7]*=e,t[11]*=e,t[15]*=e,this}determinant(){const e=this.elements,t=e[0],r=e[4],i=e[8],s=e[12],a=e[1],o=e[5],l=e[9],c=e[13],u=e[2],f=e[6],h=e[10],d=e[14],m=e[3],g=e[7],p=e[11],_=e[15],M=l*d-c*h,y=o*d-c*f,v=o*h-l*f,S=a*d-c*u,b=a*h-l*u,E=a*f-o*u;return t*(g*M-p*y+_*v)-r*(m*M-p*S+_*b)+i*(m*y-g*S+_*E)-s*(m*v-g*b+p*E)}transpose(){const e=this.elements;let t;return t=e[1],e[1]=e[4],e[4]=t,t=e[2],e[2]=e[8],e[8]=t,t=e[6],e[6]=e[9],e[9]=t,t=e[3],e[3]=e[12],e[12]=t,t=e[7],e[7]=e[13],e[13]=t,t=e[11],e[11]=e[14],e[14]=t,this}setPosition(e,t,r){const i=this.elements;return e.isVector3?(i[12]=e.x,i[13]=e.y,i[14]=e.z):(i[12]=e,i[13]=t,i[14]=r),this}invert(){const e=this.elements,t=e[0],r=e[1],i=e[2],s=e[3],a=e[4],o=e[5],l=e[6],c=e[7],u=e[8],f=e[9],h=e[10],d=e[11],m=e[12],g=e[13],p=e[14],_=e[15],M=t*o-r*a,y=t*l-i*a,v=t*c-s*a,S=r*l-i*o,b=r*c-s*o,E=i*c-s*l,x=u*g-f*m,w=u*p-h*m,R=u*_-d*m,L=f*p-h*g,A=f*_-d*g,U=h*_-d*p,P=M*U-y*A+v*L+S*R-b*w+E*x;if(P===0)return this.set(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);const I=1/P;return e[0]=(o*U-l*A+c*L)*I,e[1]=(i*A-r*U-s*L)*I,e[2]=(g*E-p*b+_*S)*I,e[3]=(h*b-f*E-d*S)*I,e[4]=(l*R-a*U-c*w)*I,e[5]=(t*U-i*R+s*w)*I,e[6]=(p*v-m*E-_*y)*I,e[7]=(u*E-h*v+d*y)*I,e[8]=(a*A-o*R+c*x)*I,e[9]=(r*R-t*A-s*x)*I,e[10]=(m*b-g*v+_*M)*I,e[11]=(f*v-u*b-d*M)*I,e[12]=(o*w-a*L-l*x)*I,e[13]=(t*L-r*w+i*x)*I,e[14]=(g*y-m*S-p*M)*I,e[15]=(u*S-f*y+h*M)*I,this}scale(e){const t=this.elements,r=e.x,i=e.y,s=e.z;return t[0]*=r,t[4]*=i,t[8]*=s,t[1]*=r,t[5]*=i,t[9]*=s,t[2]*=r,t[6]*=i,t[10]*=s,t[3]*=r,t[7]*=i,t[11]*=s,this}getMaxScaleOnAxis(){const e=this.elements,t=e[0]*e[0]+e[1]*e[1]+e[2]*e[2],r=e[4]*e[4]+e[5]*e[5]+e[6]*e[6],i=e[8]*e[8]+e[9]*e[9]+e[10]*e[10];return Math.sqrt(Math.max(t,r,i))}makeTranslation(e,t,r){return e.isVector3?this.set(1,0,0,e.x,0,1,0,e.y,0,0,1,e.z,0,0,0,1):this.set(1,0,0,e,0,1,0,t,0,0,1,r,0,0,0,1),this}makeRotationX(e){const t=Math.cos(e),r=Math.sin(e);return this.set(1,0,0,0,0,t,-r,0,0,r,t,0,0,0,0,1),this}makeRotationY(e){const t=Math.cos(e),r=Math.sin(e);return this.set(t,0,r,0,0,1,0,0,-r,0,t,0,0,0,0,1),this}makeRotationZ(e){const t=Math.cos(e),r=Math.sin(e);return this.set(t,-r,0,0,r,t,0,0,0,0,1,0,0,0,0,1),this}makeRotationAxis(e,t){const r=Math.cos(t),i=Math.sin(t),s=1-r,a=e.x,o=e.y,l=e.z,c=s*a,u=s*o;return this.set(c*a+r,c*o-i*l,c*l+i*o,0,c*o+i*l,u*o+r,u*l-i*a,0,c*l-i*o,u*l+i*a,s*l*l+r,0,0,0,0,1),this}makeScale(e,t,r){return this.set(e,0,0,0,0,t,0,0,0,0,r,0,0,0,0,1),this}makeShear(e,t,r,i,s,a){return this.set(1,r,s,0,e,1,a,0,t,i,1,0,0,0,0,1),this}compose(e,t,r){const i=this.elements,s=t._x,a=t._y,o=t._z,l=t._w,c=s+s,u=a+a,f=o+o,h=s*c,d=s*u,m=s*f,g=a*u,p=a*f,_=o*f,M=l*c,y=l*u,v=l*f,S=r.x,b=r.y,E=r.z;return i[0]=(1-(g+_))*S,i[1]=(d+v)*S,i[2]=(m-y)*S,i[3]=0,i[4]=(d-v)*b,i[5]=(1-(h+_))*b,i[6]=(p+M)*b,i[7]=0,i[8]=(m+y)*E,i[9]=(p-M)*E,i[10]=(1-(h+g))*E,i[11]=0,i[12]=e.x,i[13]=e.y,i[14]=e.z,i[15]=1,this}decompose(e,t,r){const i=this.elements;e.x=i[12],e.y=i[13],e.z=i[14];const s=this.determinant();if(s===0)return r.set(1,1,1),t.identity(),this;let a=ls.set(i[0],i[1],i[2]).length();const o=ls.set(i[4],i[5],i[6]).length(),l=ls.set(i[8],i[9],i[10]).length();s<0&&(a=-a),si.copy(this);const c=1/a,u=1/o,f=1/l;return si.elements[0]*=c,si.elements[1]*=c,si.elements[2]*=c,si.elements[4]*=u,si.elements[5]*=u,si.elements[6]*=u,si.elements[8]*=f,si.elements[9]*=f,si.elements[10]*=f,t.setFromRotationMatrix(si),r.x=a,r.y=o,r.z=l,this}makePerspective(e,t,r,i,s,a,o=Ai,l=!1){const c=this.elements,u=2*s/(t-e),f=2*s/(r-i),h=(t+e)/(t-e),d=(r+i)/(r-i);let m,g;if(l)m=s/(a-s),g=a*s/(a-s);else if(o===Ai)m=-(a+s)/(a-s),g=-2*a*s/(a-s);else if(o===ol)m=-a/(a-s),g=-a*s/(a-s);else throw new Error("THREE.Matrix4.makePerspective(): Invalid coordinate system: "+o);return c[0]=u,c[4]=0,c[8]=h,c[12]=0,c[1]=0,c[5]=f,c[9]=d,c[13]=0,c[2]=0,c[6]=0,c[10]=m,c[14]=g,c[3]=0,c[7]=0,c[11]=-1,c[15]=0,this}makeOrthographic(e,t,r,i,s,a,o=Ai,l=!1){const c=this.elements,u=2/(t-e),f=2/(r-i),h=-(t+e)/(t-e),d=-(r+i)/(r-i);let m,g;if(l)m=1/(a-s),g=a/(a-s);else if(o===Ai)m=-2/(a-s),g=-(a+s)/(a-s);else if(o===ol)m=-1/(a-s),g=-s/(a-s);else throw new Error("THREE.Matrix4.makeOrthographic(): Invalid coordinate system: "+o);return c[0]=u,c[4]=0,c[8]=0,c[12]=h,c[1]=0,c[5]=f,c[9]=0,c[13]=d,c[2]=0,c[6]=0,c[10]=m,c[14]=g,c[3]=0,c[7]=0,c[11]=0,c[15]=1,this}equals(e){const t=this.elements,r=e.elements;for(let i=0;i<16;i++)if(t[i]!==r[i])return!1;return!0}fromArray(e,t=0){for(let r=0;r<16;r++)this.elements[r]=e[r+t];return this}toArray(e=[],t=0){const r=this.elements;return e[t]=r[0],e[t+1]=r[1],e[t+2]=r[2],e[t+3]=r[3],e[t+4]=r[4],e[t+5]=r[5],e[t+6]=r[6],e[t+7]=r[7],e[t+8]=r[8],e[t+9]=r[9],e[t+10]=r[10],e[t+11]=r[11],e[t+12]=r[12],e[t+13]=r[13],e[t+14]=r[14],e[t+15]=r[15],e}};wl.prototype.isMatrix4=!0;let Ot=wl;const ls=new X,si=new Ot,U_=new X(0,0,0),L_=new X(1,1,1),tr=new X,ao=new X,Nn=new X,rd=new Ot,sd=new vr;class Zr{constructor(e=0,t=0,r=0,i=Zr.DEFAULT_ORDER){this.isEuler=!0,this._x=e,this._y=t,this._z=r,this._order=i}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get order(){return this._order}set order(e){this._order=e,this._onChangeCallback()}set(e,t,r,i=this._order){return this._x=e,this._y=t,this._z=r,this._order=i,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._order)}copy(e){return this._x=e._x,this._y=e._y,this._z=e._z,this._order=e._order,this._onChangeCallback(),this}setFromRotationMatrix(e,t=this._order,r=!0){const i=e.elements,s=i[0],a=i[4],o=i[8],l=i[1],c=i[5],u=i[9],f=i[2],h=i[6],d=i[10];switch(t){case"XYZ":this._y=Math.asin(at(o,-1,1)),Math.abs(o)<.9999999?(this._x=Math.atan2(-u,d),this._z=Math.atan2(-a,s)):(this._x=Math.atan2(h,c),this._z=0);break;case"YXZ":this._x=Math.asin(-at(u,-1,1)),Math.abs(u)<.9999999?(this._y=Math.atan2(o,d),this._z=Math.atan2(l,c)):(this._y=Math.atan2(-f,s),this._z=0);break;case"ZXY":this._x=Math.asin(at(h,-1,1)),Math.abs(h)<.9999999?(this._y=Math.atan2(-f,d),this._z=Math.atan2(-a,c)):(this._y=0,this._z=Math.atan2(l,s));break;case"ZYX":this._y=Math.asin(-at(f,-1,1)),Math.abs(f)<.9999999?(this._x=Math.atan2(h,d),this._z=Math.atan2(l,s)):(this._x=0,this._z=Math.atan2(-a,c));break;case"YZX":this._z=Math.asin(at(l,-1,1)),Math.abs(l)<.9999999?(this._x=Math.atan2(-u,c),this._y=Math.atan2(-f,s)):(this._x=0,this._y=Math.atan2(o,d));break;case"XZY":this._z=Math.asin(-at(a,-1,1)),Math.abs(a)<.9999999?(this._x=Math.atan2(h,c),this._y=Math.atan2(o,s)):(this._x=Math.atan2(-u,d),this._y=0);break;default:$e("Euler: .setFromRotationMatrix() encountered an unknown order: "+t)}return this._order=t,r===!0&&this._onChangeCallback(),this}setFromQuaternion(e,t,r){return rd.makeRotationFromQuaternion(e),this.setFromRotationMatrix(rd,t,r)}setFromVector3(e,t=this._order){return this.set(e.x,e.y,e.z,t)}reorder(e){return sd.setFromEuler(this),this.setFromQuaternion(sd,e)}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._order===this._order}fromArray(e){return this._x=e[0],this._y=e[1],this._z=e[2],e[3]!==void 0&&(this._order=e[3]),this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._order,e}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._order}}Zr.DEFAULT_ORDER="XYZ";class Rm{constructor(){this.mask=1}set(e){this.mask=(1<<e|0)>>>0}enable(e){this.mask|=1<<e|0}enableAll(){this.mask=-1}toggle(e){this.mask^=1<<e|0}disable(e){this.mask&=~(1<<e|0)}disableAll(){this.mask=0}test(e){return(this.mask&e.mask)!==0}isEnabled(e){return(this.mask&(1<<e|0))!==0}}let I_=0;const ad=new X,cs=new vr,Fi=new Ot,oo=new X,ua=new X,F_=new X,N_=new vr,od=new X(1,0,0),ld=new X(0,1,0),cd=new X(0,0,1),ud={type:"added"},O_={type:"removed"},us={type:"childadded",child:null},cc={type:"childremoved",child:null};class mn extends hi{constructor(){super(),this.isObject3D=!0,Object.defineProperty(this,"id",{value:I_++}),this.uuid=pr(),this.name="",this.type="Object3D",this.parent=null,this.children=[],this.up=mn.DEFAULT_UP.clone();const e=new X,t=new Zr,r=new vr,i=new X(1,1,1);function s(){r.setFromEuler(t,!1)}function a(){t.setFromQuaternion(r,void 0,!1)}t._onChange(s),r._onChange(a),Object.defineProperties(this,{position:{configurable:!0,enumerable:!0,value:e},rotation:{configurable:!0,enumerable:!0,value:t},quaternion:{configurable:!0,enumerable:!0,value:r},scale:{configurable:!0,enumerable:!0,value:i},modelViewMatrix:{value:new Ot},normalMatrix:{value:new nt}}),this.matrix=new Ot,this.matrixWorld=new Ot,this.matrixAutoUpdate=mn.DEFAULT_MATRIX_AUTO_UPDATE,this.matrixWorldAutoUpdate=mn.DEFAULT_MATRIX_WORLD_AUTO_UPDATE,this.matrixWorldNeedsUpdate=!1,this.layers=new Rm,this.visible=!0,this.castShadow=!1,this.receiveShadow=!1,this.frustumCulled=!0,this.renderOrder=0,this.animations=[],this.customDepthMaterial=void 0,this.customDistanceMaterial=void 0,this.static=!1,this.userData={},this.pivot=null}onBeforeShadow(){}onAfterShadow(){}onBeforeRender(){}onAfterRender(){}applyMatrix4(e){this.matrixAutoUpdate&&this.updateMatrix(),this.matrix.premultiply(e),this.matrix.decompose(this.position,this.quaternion,this.scale)}applyQuaternion(e){return this.quaternion.premultiply(e),this}setRotationFromAxisAngle(e,t){this.quaternion.setFromAxisAngle(e,t)}setRotationFromEuler(e){this.quaternion.setFromEuler(e,!0)}setRotationFromMatrix(e){this.quaternion.setFromRotationMatrix(e)}setRotationFromQuaternion(e){this.quaternion.copy(e)}rotateOnAxis(e,t){return cs.setFromAxisAngle(e,t),this.quaternion.multiply(cs),this}rotateOnWorldAxis(e,t){return cs.setFromAxisAngle(e,t),this.quaternion.premultiply(cs),this}rotateX(e){return this.rotateOnAxis(od,e)}rotateY(e){return this.rotateOnAxis(ld,e)}rotateZ(e){return this.rotateOnAxis(cd,e)}translateOnAxis(e,t){return ad.copy(e).applyQuaternion(this.quaternion),this.position.add(ad.multiplyScalar(t)),this}translateX(e){return this.translateOnAxis(od,e)}translateY(e){return this.translateOnAxis(ld,e)}translateZ(e){return this.translateOnAxis(cd,e)}localToWorld(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(this.matrixWorld)}worldToLocal(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(Fi.copy(this.matrixWorld).invert())}lookAt(e,t,r){e.isVector3?oo.copy(e):oo.set(e,t,r);const i=this.parent;this.updateWorldMatrix(!0,!1),ua.setFromMatrixPosition(this.matrixWorld),this.isCamera||this.isLight?Fi.lookAt(ua,oo,this.up):Fi.lookAt(oo,ua,this.up),this.quaternion.setFromRotationMatrix(Fi),i&&(Fi.extractRotation(i.matrixWorld),cs.setFromRotationMatrix(Fi),this.quaternion.premultiply(cs.invert()))}add(e){if(arguments.length>1){for(let t=0;t<arguments.length;t++)this.add(arguments[t]);return this}return e===this?(ft("Object3D.add: object can't be added as a child of itself.",e),this):(e&&e.isObject3D?(e.removeFromParent(),e.parent=this,this.children.push(e),e.dispatchEvent(ud),us.child=e,this.dispatchEvent(us),us.child=null):ft("Object3D.add: object not an instance of THREE.Object3D.",e),this)}remove(e){if(arguments.length>1){for(let r=0;r<arguments.length;r++)this.remove(arguments[r]);return this}const t=this.children.indexOf(e);return t!==-1&&(e.parent=null,this.children.splice(t,1),e.dispatchEvent(O_),cc.child=e,this.dispatchEvent(cc),cc.child=null),this}removeFromParent(){const e=this.parent;return e!==null&&e.remove(this),this}clear(){return this.remove(...this.children)}attach(e){return this.updateWorldMatrix(!0,!1),Fi.copy(this.matrixWorld).invert(),e.parent!==null&&(e.parent.updateWorldMatrix(!0,!1),Fi.multiply(e.parent.matrixWorld)),e.applyMatrix4(Fi),e.removeFromParent(),e.parent=this,this.children.push(e),e.updateWorldMatrix(!1,!0),e.dispatchEvent(ud),us.child=e,this.dispatchEvent(us),us.child=null,this}getObjectById(e){return this.getObjectByProperty("id",e)}getObjectByName(e){return this.getObjectByProperty("name",e)}getObjectByProperty(e,t){if(this[e]===t)return this;for(let r=0,i=this.children.length;r<i;r++){const a=this.children[r].getObjectByProperty(e,t);if(a!==void 0)return a}}getObjectsByProperty(e,t,r=[]){this[e]===t&&r.push(this);const i=this.children;for(let s=0,a=i.length;s<a;s++)i[s].getObjectsByProperty(e,t,r);return r}getWorldPosition(e){return this.updateWorldMatrix(!0,!1),e.setFromMatrixPosition(this.matrixWorld)}getWorldQuaternion(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(ua,e,F_),e}getWorldScale(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(ua,N_,e),e}getWorldDirection(e){this.updateWorldMatrix(!0,!1);const t=this.matrixWorld.elements;return e.set(t[8],t[9],t[10]).normalize()}raycast(){}traverse(e){e(this);const t=this.children;for(let r=0,i=t.length;r<i;r++)t[r].traverse(e)}traverseVisible(e){if(this.visible===!1)return;e(this);const t=this.children;for(let r=0,i=t.length;r<i;r++)t[r].traverseVisible(e)}traverseAncestors(e){const t=this.parent;t!==null&&(e(t),t.traverseAncestors(e))}updateMatrix(){this.matrix.compose(this.position,this.quaternion,this.scale);const e=this.pivot;if(e!==null){const t=e.x,r=e.y,i=e.z,s=this.matrix.elements;s[12]+=t-s[0]*t-s[4]*r-s[8]*i,s[13]+=r-s[1]*t-s[5]*r-s[9]*i,s[14]+=i-s[2]*t-s[6]*r-s[10]*i}this.matrixWorldNeedsUpdate=!0}updateMatrixWorld(e){this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||e)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,e=!0);const t=this.children;for(let r=0,i=t.length;r<i;r++)t[r].updateMatrixWorld(e)}updateWorldMatrix(e,t){const r=this.parent;if(e===!0&&r!==null&&r.updateWorldMatrix(!0,!1),this.matrixAutoUpdate&&this.updateMatrix(),this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),t===!0){const i=this.children;for(let s=0,a=i.length;s<a;s++)i[s].updateWorldMatrix(!1,!0)}}toJSON(e){const t=e===void 0||typeof e=="string",r={};t&&(e={geometries:{},materials:{},textures:{},images:{},shapes:{},skeletons:{},animations:{},nodes:{}},r.metadata={version:4.7,type:"Object",generator:"Object3D.toJSON"});const i={};i.uuid=this.uuid,i.type=this.type,this.name!==""&&(i.name=this.name),this.castShadow===!0&&(i.castShadow=!0),this.receiveShadow===!0&&(i.receiveShadow=!0),this.visible===!1&&(i.visible=!1),this.frustumCulled===!1&&(i.frustumCulled=!1),this.renderOrder!==0&&(i.renderOrder=this.renderOrder),this.static!==!1&&(i.static=this.static),Object.keys(this.userData).length>0&&(i.userData=this.userData),i.layers=this.layers.mask,i.matrix=this.matrix.toArray(),i.up=this.up.toArray(),this.pivot!==null&&(i.pivot=this.pivot.toArray()),this.matrixAutoUpdate===!1&&(i.matrixAutoUpdate=!1),this.morphTargetDictionary!==void 0&&(i.morphTargetDictionary=Object.assign({},this.morphTargetDictionary)),this.morphTargetInfluences!==void 0&&(i.morphTargetInfluences=this.morphTargetInfluences.slice()),this.isInstancedMesh&&(i.type="InstancedMesh",i.count=this.count,i.instanceMatrix=this.instanceMatrix.toJSON(),this.instanceColor!==null&&(i.instanceColor=this.instanceColor.toJSON())),this.isBatchedMesh&&(i.type="BatchedMesh",i.perObjectFrustumCulled=this.perObjectFrustumCulled,i.sortObjects=this.sortObjects,i.drawRanges=this._drawRanges,i.reservedRanges=this._reservedRanges,i.geometryInfo=this._geometryInfo.map(o=>({...o,boundingBox:o.boundingBox?o.boundingBox.toJSON():void 0,boundingSphere:o.boundingSphere?o.boundingSphere.toJSON():void 0})),i.instanceInfo=this._instanceInfo.map(o=>({...o})),i.availableInstanceIds=this._availableInstanceIds.slice(),i.availableGeometryIds=this._availableGeometryIds.slice(),i.nextIndexStart=this._nextIndexStart,i.nextVertexStart=this._nextVertexStart,i.geometryCount=this._geometryCount,i.maxInstanceCount=this._maxInstanceCount,i.maxVertexCount=this._maxVertexCount,i.maxIndexCount=this._maxIndexCount,i.geometryInitialized=this._geometryInitialized,i.matricesTexture=this._matricesTexture.toJSON(e),i.indirectTexture=this._indirectTexture.toJSON(e),this._colorsTexture!==null&&(i.colorsTexture=this._colorsTexture.toJSON(e)),this.boundingSphere!==null&&(i.boundingSphere=this.boundingSphere.toJSON()),this.boundingBox!==null&&(i.boundingBox=this.boundingBox.toJSON()));function s(o,l){return o[l.uuid]===void 0&&(o[l.uuid]=l.toJSON(e)),l.uuid}if(this.isScene)this.background&&(this.background.isColor?i.background=this.background.toJSON():this.background.isTexture&&(i.background=this.background.toJSON(e).uuid)),this.environment&&this.environment.isTexture&&this.environment.isRenderTargetTexture!==!0&&(i.environment=this.environment.toJSON(e).uuid);else if(this.isMesh||this.isLine||this.isPoints){i.geometry=s(e.geometries,this.geometry);const o=this.geometry.parameters;if(o!==void 0&&o.shapes!==void 0){const l=o.shapes;if(Array.isArray(l))for(let c=0,u=l.length;c<u;c++){const f=l[c];s(e.shapes,f)}else s(e.shapes,l)}}if(this.isSkinnedMesh&&(i.bindMode=this.bindMode,i.bindMatrix=this.bindMatrix.toArray(),this.skeleton!==void 0&&(s(e.skeletons,this.skeleton),i.skeleton=this.skeleton.uuid)),this.material!==void 0)if(Array.isArray(this.material)){const o=[];for(let l=0,c=this.material.length;l<c;l++)o.push(s(e.materials,this.material[l]));i.material=o}else i.material=s(e.materials,this.material);if(this.children.length>0){i.children=[];for(let o=0;o<this.children.length;o++)i.children.push(this.children[o].toJSON(e).object)}if(this.animations.length>0){i.animations=[];for(let o=0;o<this.animations.length;o++){const l=this.animations[o];i.animations.push(s(e.animations,l))}}if(t){const o=a(e.geometries),l=a(e.materials),c=a(e.textures),u=a(e.images),f=a(e.shapes),h=a(e.skeletons),d=a(e.animations),m=a(e.nodes);o.length>0&&(r.geometries=o),l.length>0&&(r.materials=l),c.length>0&&(r.textures=c),u.length>0&&(r.images=u),f.length>0&&(r.shapes=f),h.length>0&&(r.skeletons=h),d.length>0&&(r.animations=d),m.length>0&&(r.nodes=m)}return r.object=i,r;function a(o){const l=[];for(const c in o){const u=o[c];delete u.metadata,l.push(u)}return l}}clone(e){return new this.constructor().copy(this,e)}copy(e,t=!0){if(this.name=e.name,this.up.copy(e.up),this.position.copy(e.position),this.rotation.order=e.rotation.order,this.quaternion.copy(e.quaternion),this.scale.copy(e.scale),this.pivot=e.pivot!==null?e.pivot.clone():null,this.matrix.copy(e.matrix),this.matrixWorld.copy(e.matrixWorld),this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrixWorldAutoUpdate=e.matrixWorldAutoUpdate,this.matrixWorldNeedsUpdate=e.matrixWorldNeedsUpdate,this.layers.mask=e.layers.mask,this.visible=e.visible,this.castShadow=e.castShadow,this.receiveShadow=e.receiveShadow,this.frustumCulled=e.frustumCulled,this.renderOrder=e.renderOrder,this.static=e.static,this.animations=e.animations.slice(),this.userData=JSON.parse(JSON.stringify(e.userData)),t===!0)for(let r=0;r<e.children.length;r++){const i=e.children[r];this.add(i.clone())}return this}}mn.DEFAULT_UP=new X(0,1,0);mn.DEFAULT_MATRIX_AUTO_UPDATE=!0;mn.DEFAULT_MATRIX_WORLD_AUTO_UPDATE=!0;class Ta extends mn{constructor(){super(),this.isGroup=!0,this.type="Group"}}const B_={type:"move"};class uc{constructor(){this._targetRay=null,this._grip=null,this._hand=null}getHandSpace(){return this._hand===null&&(this._hand=new Ta,this._hand.matrixAutoUpdate=!1,this._hand.visible=!1,this._hand.joints={},this._hand.inputState={pinching:!1}),this._hand}getTargetRaySpace(){return this._targetRay===null&&(this._targetRay=new Ta,this._targetRay.matrixAutoUpdate=!1,this._targetRay.visible=!1,this._targetRay.hasLinearVelocity=!1,this._targetRay.linearVelocity=new X,this._targetRay.hasAngularVelocity=!1,this._targetRay.angularVelocity=new X),this._targetRay}getGripSpace(){return this._grip===null&&(this._grip=new Ta,this._grip.matrixAutoUpdate=!1,this._grip.visible=!1,this._grip.hasLinearVelocity=!1,this._grip.linearVelocity=new X,this._grip.hasAngularVelocity=!1,this._grip.angularVelocity=new X,this._grip.eventsEnabled=!1),this._grip}dispatchEvent(e){return this._targetRay!==null&&this._targetRay.dispatchEvent(e),this._grip!==null&&this._grip.dispatchEvent(e),this._hand!==null&&this._hand.dispatchEvent(e),this}connect(e){if(e&&e.hand){const t=this._hand;if(t)for(const r of e.hand.values())this._getHandJoint(t,r)}return this.dispatchEvent({type:"connected",data:e}),this}disconnect(e){return this.dispatchEvent({type:"disconnected",data:e}),this._targetRay!==null&&(this._targetRay.visible=!1),this._grip!==null&&(this._grip.visible=!1),this._hand!==null&&(this._hand.visible=!1),this}update(e,t,r){let i=null,s=null,a=null;const o=this._targetRay,l=this._grip,c=this._hand;if(e&&t.session.visibilityState!=="visible-blurred"){if(c&&e.hand){a=!0;for(const g of e.hand.values()){const p=t.getJointPose(g,r),_=this._getHandJoint(c,g);p!==null&&(_.matrix.fromArray(p.transform.matrix),_.matrix.decompose(_.position,_.rotation,_.scale),_.matrixWorldNeedsUpdate=!0,_.jointRadius=p.radius),_.visible=p!==null}const u=c.joints["index-finger-tip"],f=c.joints["thumb-tip"],h=u.position.distanceTo(f.position),d=.02,m=.005;c.inputState.pinching&&h>d+m?(c.inputState.pinching=!1,this.dispatchEvent({type:"pinchend",handedness:e.handedness,target:this})):!c.inputState.pinching&&h<=d-m&&(c.inputState.pinching=!0,this.dispatchEvent({type:"pinchstart",handedness:e.handedness,target:this}))}else l!==null&&e.gripSpace&&(s=t.getPose(e.gripSpace,r),s!==null&&(l.matrix.fromArray(s.transform.matrix),l.matrix.decompose(l.position,l.rotation,l.scale),l.matrixWorldNeedsUpdate=!0,s.linearVelocity?(l.hasLinearVelocity=!0,l.linearVelocity.copy(s.linearVelocity)):l.hasLinearVelocity=!1,s.angularVelocity?(l.hasAngularVelocity=!0,l.angularVelocity.copy(s.angularVelocity)):l.hasAngularVelocity=!1,l.eventsEnabled&&l.dispatchEvent({type:"gripUpdated",data:e,target:this})));o!==null&&(i=t.getPose(e.targetRaySpace,r),i===null&&s!==null&&(i=s),i!==null&&(o.matrix.fromArray(i.transform.matrix),o.matrix.decompose(o.position,o.rotation,o.scale),o.matrixWorldNeedsUpdate=!0,i.linearVelocity?(o.hasLinearVelocity=!0,o.linearVelocity.copy(i.linearVelocity)):o.hasLinearVelocity=!1,i.angularVelocity?(o.hasAngularVelocity=!0,o.angularVelocity.copy(i.angularVelocity)):o.hasAngularVelocity=!1,this.dispatchEvent(B_)))}return o!==null&&(o.visible=i!==null),l!==null&&(l.visible=s!==null),c!==null&&(c.visible=a!==null),this}_getHandJoint(e,t){if(e.joints[t.jointName]===void 0){const r=new Ta;r.matrixAutoUpdate=!1,r.visible=!1,e.joints[t.jointName]=r,e.add(r)}return e.joints[t.jointName]}}const Cm={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},nr={h:0,s:0,l:0},lo={h:0,s:0,l:0};function hc(n,e,t){return t<0&&(t+=1),t>1&&(t-=1),t<1/6?n+(e-n)*6*t:t<1/2?e:t<2/3?n+(e-n)*6*(2/3-t):n}class lt{constructor(e,t,r){return this.isColor=!0,this.r=1,this.g=1,this.b=1,this.set(e,t,r)}set(e,t,r){if(t===void 0&&r===void 0){const i=e;i&&i.isColor?this.copy(i):typeof i=="number"?this.setHex(i):typeof i=="string"&&this.setStyle(i)}else this.setRGB(e,t,r);return this}setScalar(e){return this.r=e,this.g=e,this.b=e,this}setHex(e,t=bt){return e=Math.floor(e),this.r=(e>>16&255)/255,this.g=(e>>8&255)/255,this.b=(e&255)/255,ut.colorSpaceToWorking(this,t),this}setRGB(e,t,r,i=ut.workingColorSpace){return this.r=e,this.g=t,this.b=r,ut.colorSpaceToWorking(this,i),this}setHSL(e,t,r,i=ut.workingColorSpace){if(e=T_(e,1),t=at(t,0,1),r=at(r,0,1),t===0)this.r=this.g=this.b=r;else{const s=r<=.5?r*(1+t):r+t-r*t,a=2*r-s;this.r=hc(a,s,e+1/3),this.g=hc(a,s,e),this.b=hc(a,s,e-1/3)}return ut.colorSpaceToWorking(this,i),this}setStyle(e,t=bt){function r(s){s!==void 0&&parseFloat(s)<1&&$e("Color: Alpha component of "+e+" will be ignored.")}let i;if(i=/^(\w+)\(([^\)]*)\)/.exec(e)){let s;const a=i[1],o=i[2];switch(a){case"rgb":case"rgba":if(s=/^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return r(s[4]),this.setRGB(Math.min(255,parseInt(s[1],10))/255,Math.min(255,parseInt(s[2],10))/255,Math.min(255,parseInt(s[3],10))/255,t);if(s=/^\s*(\d+)\%\s*,\s*(\d+)\%\s*,\s*(\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return r(s[4]),this.setRGB(Math.min(100,parseInt(s[1],10))/100,Math.min(100,parseInt(s[2],10))/100,Math.min(100,parseInt(s[3],10))/100,t);break;case"hsl":case"hsla":if(s=/^\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\%\s*,\s*(\d*\.?\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return r(s[4]),this.setHSL(parseFloat(s[1])/360,parseFloat(s[2])/100,parseFloat(s[3])/100,t);break;default:$e("Color: Unknown color model "+e)}}else if(i=/^\#([A-Fa-f\d]+)$/.exec(e)){const s=i[1],a=s.length;if(a===3)return this.setRGB(parseInt(s.charAt(0),16)/15,parseInt(s.charAt(1),16)/15,parseInt(s.charAt(2),16)/15,t);if(a===6)return this.setHex(parseInt(s,16),t);$e("Color: Invalid hex color "+e)}else if(e&&e.length>0)return this.setColorName(e,t);return this}setColorName(e,t=bt){const r=Cm[e.toLowerCase()];return r!==void 0?this.setHex(r,t):$e("Color: Unknown color "+e),this}clone(){return new this.constructor(this.r,this.g,this.b)}copy(e){return this.r=e.r,this.g=e.g,this.b=e.b,this}copySRGBToLinear(e){return this.r=Vi(e.r),this.g=Vi(e.g),this.b=Vi(e.b),this}copyLinearToSRGB(e){return this.r=Ds(e.r),this.g=Ds(e.g),this.b=Ds(e.b),this}convertSRGBToLinear(){return this.copySRGBToLinear(this),this}convertLinearToSRGB(){return this.copyLinearToSRGB(this),this}getHex(e=bt){return ut.workingToColorSpace(dn.copy(this),e),Math.round(at(dn.r*255,0,255))*65536+Math.round(at(dn.g*255,0,255))*256+Math.round(at(dn.b*255,0,255))}getHexString(e=bt){return("000000"+this.getHex(e).toString(16)).slice(-6)}getHSL(e,t=ut.workingColorSpace){ut.workingToColorSpace(dn.copy(this),t);const r=dn.r,i=dn.g,s=dn.b,a=Math.max(r,i,s),o=Math.min(r,i,s);let l,c;const u=(o+a)/2;if(o===a)l=0,c=0;else{const f=a-o;switch(c=u<=.5?f/(a+o):f/(2-a-o),a){case r:l=(i-s)/f+(i<s?6:0);break;case i:l=(s-r)/f+2;break;case s:l=(r-i)/f+4;break}l/=6}return e.h=l,e.s=c,e.l=u,e}getRGB(e,t=ut.workingColorSpace){return ut.workingToColorSpace(dn.copy(this),t),e.r=dn.r,e.g=dn.g,e.b=dn.b,e}getStyle(e=bt){ut.workingToColorSpace(dn.copy(this),e);const t=dn.r,r=dn.g,i=dn.b;return e!==bt?`color(${e} ${t.toFixed(3)} ${r.toFixed(3)} ${i.toFixed(3)})`:`rgb(${Math.round(t*255)},${Math.round(r*255)},${Math.round(i*255)})`}offsetHSL(e,t,r){return this.getHSL(nr),this.setHSL(nr.h+e,nr.s+t,nr.l+r)}add(e){return this.r+=e.r,this.g+=e.g,this.b+=e.b,this}addColors(e,t){return this.r=e.r+t.r,this.g=e.g+t.g,this.b=e.b+t.b,this}addScalar(e){return this.r+=e,this.g+=e,this.b+=e,this}sub(e){return this.r=Math.max(0,this.r-e.r),this.g=Math.max(0,this.g-e.g),this.b=Math.max(0,this.b-e.b),this}multiply(e){return this.r*=e.r,this.g*=e.g,this.b*=e.b,this}multiplyScalar(e){return this.r*=e,this.g*=e,this.b*=e,this}lerp(e,t){return this.r+=(e.r-this.r)*t,this.g+=(e.g-this.g)*t,this.b+=(e.b-this.b)*t,this}lerpColors(e,t,r){return this.r=e.r+(t.r-e.r)*r,this.g=e.g+(t.g-e.g)*r,this.b=e.b+(t.b-e.b)*r,this}lerpHSL(e,t){this.getHSL(nr),e.getHSL(lo);const r=rc(nr.h,lo.h,t),i=rc(nr.s,lo.s,t),s=rc(nr.l,lo.l,t);return this.setHSL(r,i,s),this}setFromVector3(e){return this.r=e.x,this.g=e.y,this.b=e.z,this}applyMatrix3(e){const t=this.r,r=this.g,i=this.b,s=e.elements;return this.r=s[0]*t+s[3]*r+s[6]*i,this.g=s[1]*t+s[4]*r+s[7]*i,this.b=s[2]*t+s[5]*r+s[8]*i,this}equals(e){return e.r===this.r&&e.g===this.g&&e.b===this.b}fromArray(e,t=0){return this.r=e[t],this.g=e[t+1],this.b=e[t+2],this}toArray(e=[],t=0){return e[t]=this.r,e[t+1]=this.g,e[t+2]=this.b,e}fromBufferAttribute(e,t){return this.r=e.getX(t),this.g=e.getY(t),this.b=e.getZ(t),this}toJSON(){return this.getHex()}*[Symbol.iterator](){yield this.r,yield this.g,yield this.b}}const dn=new lt;lt.NAMES=Cm;class uh extends mn{constructor(){super(),this.isScene=!0,this.type="Scene",this.background=null,this.environment=null,this.fog=null,this.backgroundBlurriness=0,this.backgroundIntensity=1,this.backgroundRotation=new Zr,this.environmentIntensity=1,this.environmentRotation=new Zr,this.overrideMaterial=null,typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}copy(e,t){return super.copy(e,t),e.background!==null&&(this.background=e.background.clone()),e.environment!==null&&(this.environment=e.environment.clone()),e.fog!==null&&(this.fog=e.fog.clone()),this.backgroundBlurriness=e.backgroundBlurriness,this.backgroundIntensity=e.backgroundIntensity,this.backgroundRotation.copy(e.backgroundRotation),this.environmentIntensity=e.environmentIntensity,this.environmentRotation.copy(e.environmentRotation),e.overrideMaterial!==null&&(this.overrideMaterial=e.overrideMaterial.clone()),this.matrixAutoUpdate=e.matrixAutoUpdate,this}toJSON(e){const t=super.toJSON(e);return this.fog!==null&&(t.object.fog=this.fog.toJSON()),this.backgroundBlurriness>0&&(t.object.backgroundBlurriness=this.backgroundBlurriness),this.backgroundIntensity!==1&&(t.object.backgroundIntensity=this.backgroundIntensity),t.object.backgroundRotation=this.backgroundRotation.toArray(),this.environmentIntensity!==1&&(t.object.environmentIntensity=this.environmentIntensity),t.object.environmentRotation=this.environmentRotation.toArray(),t}}const ai=new X,Ni=new X,fc=new X,Oi=new X,hs=new X,fs=new X,hd=new X,dc=new X,pc=new X,mc=new X,gc=new Ct,_c=new Ct,vc=new Ct;class $n{constructor(e=new X,t=new X,r=new X){this.a=e,this.b=t,this.c=r}static getNormal(e,t,r,i){i.subVectors(r,t),ai.subVectors(e,t),i.cross(ai);const s=i.lengthSq();return s>0?i.multiplyScalar(1/Math.sqrt(s)):i.set(0,0,0)}static getBarycoord(e,t,r,i,s){ai.subVectors(i,t),Ni.subVectors(r,t),fc.subVectors(e,t);const a=ai.dot(ai),o=ai.dot(Ni),l=ai.dot(fc),c=Ni.dot(Ni),u=Ni.dot(fc),f=a*c-o*o;if(f===0)return s.set(0,0,0),null;const h=1/f,d=(c*l-o*u)*h,m=(a*u-o*l)*h;return s.set(1-d-m,m,d)}static containsPoint(e,t,r,i){return this.getBarycoord(e,t,r,i,Oi)===null?!1:Oi.x>=0&&Oi.y>=0&&Oi.x+Oi.y<=1}static getInterpolation(e,t,r,i,s,a,o,l){return this.getBarycoord(e,t,r,i,Oi)===null?(l.x=0,l.y=0,"z"in l&&(l.z=0),"w"in l&&(l.w=0),null):(l.setScalar(0),l.addScaledVector(s,Oi.x),l.addScaledVector(a,Oi.y),l.addScaledVector(o,Oi.z),l)}static getInterpolatedAttribute(e,t,r,i,s,a){return gc.setScalar(0),_c.setScalar(0),vc.setScalar(0),gc.fromBufferAttribute(e,t),_c.fromBufferAttribute(e,r),vc.fromBufferAttribute(e,i),a.setScalar(0),a.addScaledVector(gc,s.x),a.addScaledVector(_c,s.y),a.addScaledVector(vc,s.z),a}static isFrontFacing(e,t,r,i){return ai.subVectors(r,t),Ni.subVectors(e,t),ai.cross(Ni).dot(i)<0}set(e,t,r){return this.a.copy(e),this.b.copy(t),this.c.copy(r),this}setFromPointsAndIndices(e,t,r,i){return this.a.copy(e[t]),this.b.copy(e[r]),this.c.copy(e[i]),this}setFromAttributeAndIndices(e,t,r,i){return this.a.fromBufferAttribute(e,t),this.b.fromBufferAttribute(e,r),this.c.fromBufferAttribute(e,i),this}clone(){return new this.constructor().copy(this)}copy(e){return this.a.copy(e.a),this.b.copy(e.b),this.c.copy(e.c),this}getArea(){return ai.subVectors(this.c,this.b),Ni.subVectors(this.a,this.b),ai.cross(Ni).length()*.5}getMidpoint(e){return e.addVectors(this.a,this.b).add(this.c).multiplyScalar(1/3)}getNormal(e){return $n.getNormal(this.a,this.b,this.c,e)}getPlane(e){return e.setFromCoplanarPoints(this.a,this.b,this.c)}getBarycoord(e,t){return $n.getBarycoord(e,this.a,this.b,this.c,t)}getInterpolation(e,t,r,i,s){return $n.getInterpolation(e,this.a,this.b,this.c,t,r,i,s)}containsPoint(e){return $n.containsPoint(e,this.a,this.b,this.c)}isFrontFacing(e){return $n.isFrontFacing(this.a,this.b,this.c,e)}intersectsBox(e){return e.intersectsTriangle(this)}closestPointToPoint(e,t){const r=this.a,i=this.b,s=this.c;let a,o;hs.subVectors(i,r),fs.subVectors(s,r),dc.subVectors(e,r);const l=hs.dot(dc),c=fs.dot(dc);if(l<=0&&c<=0)return t.copy(r);pc.subVectors(e,i);const u=hs.dot(pc),f=fs.dot(pc);if(u>=0&&f<=u)return t.copy(i);const h=l*f-u*c;if(h<=0&&l>=0&&u<=0)return a=l/(l-u),t.copy(r).addScaledVector(hs,a);mc.subVectors(e,s);const d=hs.dot(mc),m=fs.dot(mc);if(m>=0&&d<=m)return t.copy(s);const g=d*c-l*m;if(g<=0&&c>=0&&m<=0)return o=c/(c-m),t.copy(r).addScaledVector(fs,o);const p=u*m-d*f;if(p<=0&&f-u>=0&&d-m>=0)return hd.subVectors(s,i),o=(f-u)/(f-u+(d-m)),t.copy(i).addScaledVector(hd,o);const _=1/(p+g+h);return a=g*_,o=h*_,t.copy(r).addScaledVector(hs,a).addScaledVector(fs,o)}equals(e){return e.a.equals(this.a)&&e.b.equals(this.b)&&e.c.equals(this.c)}}class qs{constructor(e=new X(1/0,1/0,1/0),t=new X(-1/0,-1/0,-1/0)){this.isBox3=!0,this.min=e,this.max=t}set(e,t){return this.min.copy(e),this.max.copy(t),this}setFromArray(e){this.makeEmpty();for(let t=0,r=e.length;t<r;t+=3)this.expandByPoint(oi.fromArray(e,t));return this}setFromBufferAttribute(e){this.makeEmpty();for(let t=0,r=e.count;t<r;t++)this.expandByPoint(oi.fromBufferAttribute(e,t));return this}setFromPoints(e){this.makeEmpty();for(let t=0,r=e.length;t<r;t++)this.expandByPoint(e[t]);return this}setFromCenterAndSize(e,t){const r=oi.copy(t).multiplyScalar(.5);return this.min.copy(e).sub(r),this.max.copy(e).add(r),this}setFromObject(e,t=!1){return this.makeEmpty(),this.expandByObject(e,t)}clone(){return new this.constructor().copy(this)}copy(e){return this.min.copy(e.min),this.max.copy(e.max),this}makeEmpty(){return this.min.x=this.min.y=this.min.z=1/0,this.max.x=this.max.y=this.max.z=-1/0,this}isEmpty(){return this.max.x<this.min.x||this.max.y<this.min.y||this.max.z<this.min.z}getCenter(e){return this.isEmpty()?e.set(0,0,0):e.addVectors(this.min,this.max).multiplyScalar(.5)}getSize(e){return this.isEmpty()?e.set(0,0,0):e.subVectors(this.max,this.min)}expandByPoint(e){return this.min.min(e),this.max.max(e),this}expandByVector(e){return this.min.sub(e),this.max.add(e),this}expandByScalar(e){return this.min.addScalar(-e),this.max.addScalar(e),this}expandByObject(e,t=!1){e.updateWorldMatrix(!1,!1);const r=e.geometry;if(r!==void 0){const s=r.getAttribute("position");if(t===!0&&s!==void 0&&e.isInstancedMesh!==!0)for(let a=0,o=s.count;a<o;a++)e.isMesh===!0?e.getVertexPosition(a,oi):oi.fromBufferAttribute(s,a),oi.applyMatrix4(e.matrixWorld),this.expandByPoint(oi);else e.boundingBox!==void 0?(e.boundingBox===null&&e.computeBoundingBox(),co.copy(e.boundingBox)):(r.boundingBox===null&&r.computeBoundingBox(),co.copy(r.boundingBox)),co.applyMatrix4(e.matrixWorld),this.union(co)}const i=e.children;for(let s=0,a=i.length;s<a;s++)this.expandByObject(i[s],t);return this}containsPoint(e){return e.x>=this.min.x&&e.x<=this.max.x&&e.y>=this.min.y&&e.y<=this.max.y&&e.z>=this.min.z&&e.z<=this.max.z}containsBox(e){return this.min.x<=e.min.x&&e.max.x<=this.max.x&&this.min.y<=e.min.y&&e.max.y<=this.max.y&&this.min.z<=e.min.z&&e.max.z<=this.max.z}getParameter(e,t){return t.set((e.x-this.min.x)/(this.max.x-this.min.x),(e.y-this.min.y)/(this.max.y-this.min.y),(e.z-this.min.z)/(this.max.z-this.min.z))}intersectsBox(e){return e.max.x>=this.min.x&&e.min.x<=this.max.x&&e.max.y>=this.min.y&&e.min.y<=this.max.y&&e.max.z>=this.min.z&&e.min.z<=this.max.z}intersectsSphere(e){return this.clampPoint(e.center,oi),oi.distanceToSquared(e.center)<=e.radius*e.radius}intersectsPlane(e){let t,r;return e.normal.x>0?(t=e.normal.x*this.min.x,r=e.normal.x*this.max.x):(t=e.normal.x*this.max.x,r=e.normal.x*this.min.x),e.normal.y>0?(t+=e.normal.y*this.min.y,r+=e.normal.y*this.max.y):(t+=e.normal.y*this.max.y,r+=e.normal.y*this.min.y),e.normal.z>0?(t+=e.normal.z*this.min.z,r+=e.normal.z*this.max.z):(t+=e.normal.z*this.max.z,r+=e.normal.z*this.min.z),t<=-e.constant&&r>=-e.constant}intersectsTriangle(e){if(this.isEmpty())return!1;this.getCenter(ha),uo.subVectors(this.max,ha),ds.subVectors(e.a,ha),ps.subVectors(e.b,ha),ms.subVectors(e.c,ha),ir.subVectors(ps,ds),rr.subVectors(ms,ps),wr.subVectors(ds,ms);let t=[0,-ir.z,ir.y,0,-rr.z,rr.y,0,-wr.z,wr.y,ir.z,0,-ir.x,rr.z,0,-rr.x,wr.z,0,-wr.x,-ir.y,ir.x,0,-rr.y,rr.x,0,-wr.y,wr.x,0];return!xc(t,ds,ps,ms,uo)||(t=[1,0,0,0,1,0,0,0,1],!xc(t,ds,ps,ms,uo))?!1:(ho.crossVectors(ir,rr),t=[ho.x,ho.y,ho.z],xc(t,ds,ps,ms,uo))}clampPoint(e,t){return t.copy(e).clamp(this.min,this.max)}distanceToPoint(e){return this.clampPoint(e,oi).distanceTo(e)}getBoundingSphere(e){return this.isEmpty()?e.makeEmpty():(this.getCenter(e.center),e.radius=this.getSize(oi).length()*.5),e}intersect(e){return this.min.max(e.min),this.max.min(e.max),this.isEmpty()&&this.makeEmpty(),this}union(e){return this.min.min(e.min),this.max.max(e.max),this}applyMatrix4(e){return this.isEmpty()?this:(Bi[0].set(this.min.x,this.min.y,this.min.z).applyMatrix4(e),Bi[1].set(this.min.x,this.min.y,this.max.z).applyMatrix4(e),Bi[2].set(this.min.x,this.max.y,this.min.z).applyMatrix4(e),Bi[3].set(this.min.x,this.max.y,this.max.z).applyMatrix4(e),Bi[4].set(this.max.x,this.min.y,this.min.z).applyMatrix4(e),Bi[5].set(this.max.x,this.min.y,this.max.z).applyMatrix4(e),Bi[6].set(this.max.x,this.max.y,this.min.z).applyMatrix4(e),Bi[7].set(this.max.x,this.max.y,this.max.z).applyMatrix4(e),this.setFromPoints(Bi),this)}translate(e){return this.min.add(e),this.max.add(e),this}equals(e){return e.min.equals(this.min)&&e.max.equals(this.max)}toJSON(){return{min:this.min.toArray(),max:this.max.toArray()}}fromJSON(e){return this.min.fromArray(e.min),this.max.fromArray(e.max),this}}const Bi=[new X,new X,new X,new X,new X,new X,new X,new X],oi=new X,co=new qs,ds=new X,ps=new X,ms=new X,ir=new X,rr=new X,wr=new X,ha=new X,uo=new X,ho=new X,Ar=new X;function xc(n,e,t,r,i){for(let s=0,a=n.length-3;s<=a;s+=3){Ar.fromArray(n,s);const o=i.x*Math.abs(Ar.x)+i.y*Math.abs(Ar.y)+i.z*Math.abs(Ar.z),l=e.dot(Ar),c=t.dot(Ar),u=r.dot(Ar);if(Math.max(-Math.max(l,c,u),Math.min(l,c,u))>o)return!1}return!0}const Wt=new X,fo=new We;let k_=0;class kt extends hi{constructor(e,t,r=!1){if(super(),Array.isArray(e))throw new TypeError("THREE.BufferAttribute: array should be a Typed Array.");this.isBufferAttribute=!0,Object.defineProperty(this,"id",{value:k_++}),this.name="",this.array=e,this.itemSize=t,this.count=e!==void 0?e.length/t:0,this.normalized=r,this.usage=oh,this.updateRanges=[],this.gpuType=li,this.version=0}onUploadCallback(){}set needsUpdate(e){e===!0&&this.version++}setUsage(e){return this.usage=e,this}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}copy(e){return this.name=e.name,this.array=new e.array.constructor(e.array),this.itemSize=e.itemSize,this.count=e.count,this.normalized=e.normalized,this.usage=e.usage,this.gpuType=e.gpuType,this}copyAt(e,t,r){e*=this.itemSize,r*=t.itemSize;for(let i=0,s=this.itemSize;i<s;i++)this.array[e+i]=t.array[r+i];return this}copyArray(e){return this.array.set(e),this}applyMatrix3(e){if(this.itemSize===2)for(let t=0,r=this.count;t<r;t++)fo.fromBufferAttribute(this,t),fo.applyMatrix3(e),this.setXY(t,fo.x,fo.y);else if(this.itemSize===3)for(let t=0,r=this.count;t<r;t++)Wt.fromBufferAttribute(this,t),Wt.applyMatrix3(e),this.setXYZ(t,Wt.x,Wt.y,Wt.z);return this}applyMatrix4(e){for(let t=0,r=this.count;t<r;t++)Wt.fromBufferAttribute(this,t),Wt.applyMatrix4(e),this.setXYZ(t,Wt.x,Wt.y,Wt.z);return this}applyNormalMatrix(e){for(let t=0,r=this.count;t<r;t++)Wt.fromBufferAttribute(this,t),Wt.applyNormalMatrix(e),this.setXYZ(t,Wt.x,Wt.y,Wt.z);return this}transformDirection(e){for(let t=0,r=this.count;t<r;t++)Wt.fromBufferAttribute(this,t),Wt.transformDirection(e),this.setXYZ(t,Wt.x,Wt.y,Wt.z);return this}set(e,t=0){return this.array.set(e,t),this}getComponent(e,t){let r=this.array[e*this.itemSize+t];return this.normalized&&(r=Ti(r,this.array)),r}setComponent(e,t,r){return this.normalized&&(r=Mt(r,this.array)),this.array[e*this.itemSize+t]=r,this}getX(e){let t=this.array[e*this.itemSize];return this.normalized&&(t=Ti(t,this.array)),t}setX(e,t){return this.normalized&&(t=Mt(t,this.array)),this.array[e*this.itemSize]=t,this}getY(e){let t=this.array[e*this.itemSize+1];return this.normalized&&(t=Ti(t,this.array)),t}setY(e,t){return this.normalized&&(t=Mt(t,this.array)),this.array[e*this.itemSize+1]=t,this}getZ(e){let t=this.array[e*this.itemSize+2];return this.normalized&&(t=Ti(t,this.array)),t}setZ(e,t){return this.normalized&&(t=Mt(t,this.array)),this.array[e*this.itemSize+2]=t,this}getW(e){let t=this.array[e*this.itemSize+3];return this.normalized&&(t=Ti(t,this.array)),t}setW(e,t){return this.normalized&&(t=Mt(t,this.array)),this.array[e*this.itemSize+3]=t,this}setXY(e,t,r){return e*=this.itemSize,this.normalized&&(t=Mt(t,this.array),r=Mt(r,this.array)),this.array[e+0]=t,this.array[e+1]=r,this}setXYZ(e,t,r,i){return e*=this.itemSize,this.normalized&&(t=Mt(t,this.array),r=Mt(r,this.array),i=Mt(i,this.array)),this.array[e+0]=t,this.array[e+1]=r,this.array[e+2]=i,this}setXYZW(e,t,r,i,s){return e*=this.itemSize,this.normalized&&(t=Mt(t,this.array),r=Mt(r,this.array),i=Mt(i,this.array),s=Mt(s,this.array)),this.array[e+0]=t,this.array[e+1]=r,this.array[e+2]=i,this.array[e+3]=s,this}onUpload(e){return this.onUploadCallback=e,this}clone(){return new this.constructor(this.array,this.itemSize).copy(this)}toJSON(){const e={itemSize:this.itemSize,type:this.array.constructor.name,array:Array.from(this.array),normalized:this.normalized};return this.name!==""&&(e.name=this.name),this.usage!==oh&&(e.usage=this.usage),e}dispose(){this.dispatchEvent({type:"dispose"})}}class Pm extends kt{constructor(e,t,r){super(new Uint16Array(e),t,r)}}class Dm extends kt{constructor(e,t,r){super(new Uint32Array(e),t,r)}}class ui extends kt{constructor(e,t,r){super(new Float32Array(e),t,r)}}const z_=new qs,fa=new X,Mc=new X;class js{constructor(e=new X,t=-1){this.isSphere=!0,this.center=e,this.radius=t}set(e,t){return this.center.copy(e),this.radius=t,this}setFromPoints(e,t){const r=this.center;t!==void 0?r.copy(t):z_.setFromPoints(e).getCenter(r);let i=0;for(let s=0,a=e.length;s<a;s++)i=Math.max(i,r.distanceToSquared(e[s]));return this.radius=Math.sqrt(i),this}copy(e){return this.center.copy(e.center),this.radius=e.radius,this}isEmpty(){return this.radius<0}makeEmpty(){return this.center.set(0,0,0),this.radius=-1,this}containsPoint(e){return e.distanceToSquared(this.center)<=this.radius*this.radius}distanceToPoint(e){return e.distanceTo(this.center)-this.radius}intersectsSphere(e){const t=this.radius+e.radius;return e.center.distanceToSquared(this.center)<=t*t}intersectsBox(e){return e.intersectsSphere(this)}intersectsPlane(e){return Math.abs(e.distanceToPoint(this.center))<=this.radius}clampPoint(e,t){const r=this.center.distanceToSquared(e);return t.copy(e),r>this.radius*this.radius&&(t.sub(this.center).normalize(),t.multiplyScalar(this.radius).add(this.center)),t}getBoundingBox(e){return this.isEmpty()?(e.makeEmpty(),e):(e.set(this.center,this.center),e.expandByScalar(this.radius),e)}applyMatrix4(e){return this.center.applyMatrix4(e),this.radius=this.radius*e.getMaxScaleOnAxis(),this}translate(e){return this.center.add(e),this}expandByPoint(e){if(this.isEmpty())return this.center.copy(e),this.radius=0,this;fa.subVectors(e,this.center);const t=fa.lengthSq();if(t>this.radius*this.radius){const r=Math.sqrt(t),i=(r-this.radius)*.5;this.center.addScaledVector(fa,i/r),this.radius+=i}return this}union(e){return e.isEmpty()?this:this.isEmpty()?(this.copy(e),this):(this.center.equals(e.center)===!0?this.radius=Math.max(this.radius,e.radius):(Mc.subVectors(e.center,this.center).setLength(e.radius),this.expandByPoint(fa.copy(e.center).add(Mc)),this.expandByPoint(fa.copy(e.center).sub(Mc))),this)}equals(e){return e.center.equals(this.center)&&e.radius===this.radius}clone(){return new this.constructor().copy(this)}toJSON(){return{radius:this.radius,center:this.center.toArray()}}fromJSON(e){return this.radius=e.radius,this.center.fromArray(e.center),this}}let G_=0;const Kn=new Ot,Sc=new mn,gs=new X,On=new qs,da=new qs,nn=new X;class Dt extends hi{constructor(){super(),this.isBufferGeometry=!0,Object.defineProperty(this,"id",{value:G_++}),this.uuid=pr(),this.name="",this.type="BufferGeometry",this.index=null,this.indirect=null,this.indirectOffset=0,this.attributes={},this.morphAttributes={},this.morphTargetsRelative=!1,this.groups=[],this.boundingBox=null,this.boundingSphere=null,this.drawRange={start:0,count:1/0},this.userData={}}getIndex(){return this.index}setIndex(e){return Array.isArray(e)?this.index=new(M_(e)?Dm:Pm)(e,1):this.index=e,this}setIndirect(e,t=0){return this.indirect=e,this.indirectOffset=t,this}getIndirect(){return this.indirect}getAttribute(e){return this.attributes[e]}setAttribute(e,t){return this.attributes[e]=t,this}deleteAttribute(e){return delete this.attributes[e],this}hasAttribute(e){return this.attributes[e]!==void 0}addGroup(e,t,r=0){this.groups.push({start:e,count:t,materialIndex:r})}clearGroups(){this.groups=[]}setDrawRange(e,t){this.drawRange.start=e,this.drawRange.count=t}applyMatrix4(e){const t=this.attributes.position;t!==void 0&&(t.applyMatrix4(e),t.needsUpdate=!0);const r=this.attributes.normal;if(r!==void 0){const s=new nt().getNormalMatrix(e);r.applyNormalMatrix(s),r.needsUpdate=!0}const i=this.attributes.tangent;return i!==void 0&&(i.transformDirection(e),i.needsUpdate=!0),this.boundingBox!==null&&this.computeBoundingBox(),this.boundingSphere!==null&&this.computeBoundingSphere(),this}applyQuaternion(e){return Kn.makeRotationFromQuaternion(e),this.applyMatrix4(Kn),this}rotateX(e){return Kn.makeRotationX(e),this.applyMatrix4(Kn),this}rotateY(e){return Kn.makeRotationY(e),this.applyMatrix4(Kn),this}rotateZ(e){return Kn.makeRotationZ(e),this.applyMatrix4(Kn),this}translate(e,t,r){return Kn.makeTranslation(e,t,r),this.applyMatrix4(Kn),this}scale(e,t,r){return Kn.makeScale(e,t,r),this.applyMatrix4(Kn),this}lookAt(e){return Sc.lookAt(e),Sc.updateMatrix(),this.applyMatrix4(Sc.matrix),this}center(){return this.computeBoundingBox(),this.boundingBox.getCenter(gs).negate(),this.translate(gs.x,gs.y,gs.z),this}setFromPoints(e){const t=this.getAttribute("position");if(t===void 0){const r=[];for(let i=0,s=e.length;i<s;i++){const a=e[i];r.push(a.x,a.y,a.z||0)}this.setAttribute("position",new ui(r,3))}else{const r=Math.min(e.length,t.count);for(let i=0;i<r;i++){const s=e[i];t.setXYZ(i,s.x,s.y,s.z||0)}e.length>t.count&&$e("BufferGeometry: Buffer size too small for points data. Use .dispose() and create a new geometry."),t.needsUpdate=!0}return this}computeBoundingBox(){this.boundingBox===null&&(this.boundingBox=new qs);const e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){ft("BufferGeometry.computeBoundingBox(): GLBufferAttribute requires a manual bounding box.",this),this.boundingBox.set(new X(-1/0,-1/0,-1/0),new X(1/0,1/0,1/0));return}if(e!==void 0){if(this.boundingBox.setFromBufferAttribute(e),t)for(let r=0,i=t.length;r<i;r++){const s=t[r];On.setFromBufferAttribute(s),this.morphTargetsRelative?(nn.addVectors(this.boundingBox.min,On.min),this.boundingBox.expandByPoint(nn),nn.addVectors(this.boundingBox.max,On.max),this.boundingBox.expandByPoint(nn)):(this.boundingBox.expandByPoint(On.min),this.boundingBox.expandByPoint(On.max))}}else this.boundingBox.makeEmpty();(isNaN(this.boundingBox.min.x)||isNaN(this.boundingBox.min.y)||isNaN(this.boundingBox.min.z))&&ft('BufferGeometry.computeBoundingBox(): Computed min/max have NaN values. The "position" attribute is likely to have NaN values.',this)}computeBoundingSphere(){this.boundingSphere===null&&(this.boundingSphere=new js);const e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){ft("BufferGeometry.computeBoundingSphere(): GLBufferAttribute requires a manual bounding sphere.",this),this.boundingSphere.set(new X,1/0);return}if(e){const r=this.boundingSphere.center;if(On.setFromBufferAttribute(e),t)for(let s=0,a=t.length;s<a;s++){const o=t[s];da.setFromBufferAttribute(o),this.morphTargetsRelative?(nn.addVectors(On.min,da.min),On.expandByPoint(nn),nn.addVectors(On.max,da.max),On.expandByPoint(nn)):(On.expandByPoint(da.min),On.expandByPoint(da.max))}On.getCenter(r);let i=0;for(let s=0,a=e.count;s<a;s++)nn.fromBufferAttribute(e,s),i=Math.max(i,r.distanceToSquared(nn));if(t)for(let s=0,a=t.length;s<a;s++){const o=t[s],l=this.morphTargetsRelative;for(let c=0,u=o.count;c<u;c++)nn.fromBufferAttribute(o,c),l&&(gs.fromBufferAttribute(e,c),nn.add(gs)),i=Math.max(i,r.distanceToSquared(nn))}this.boundingSphere.radius=Math.sqrt(i),isNaN(this.boundingSphere.radius)&&ft('BufferGeometry.computeBoundingSphere(): Computed radius is NaN. The "position" attribute is likely to have NaN values.',this)}}computeTangents(){const e=this.index,t=this.attributes;if(e===null||t.position===void 0||t.normal===void 0||t.uv===void 0){ft("BufferGeometry: .computeTangents() failed. Missing required attributes (index, position, normal or uv)");return}const r=t.position,i=t.normal,s=t.uv;this.hasAttribute("tangent")===!1&&this.setAttribute("tangent",new kt(new Float32Array(4*r.count),4));const a=this.getAttribute("tangent"),o=[],l=[];for(let x=0;x<r.count;x++)o[x]=new X,l[x]=new X;const c=new X,u=new X,f=new X,h=new We,d=new We,m=new We,g=new X,p=new X;function _(x,w,R){c.fromBufferAttribute(r,x),u.fromBufferAttribute(r,w),f.fromBufferAttribute(r,R),h.fromBufferAttribute(s,x),d.fromBufferAttribute(s,w),m.fromBufferAttribute(s,R),u.sub(c),f.sub(c),d.sub(h),m.sub(h);const L=1/(d.x*m.y-m.x*d.y);isFinite(L)&&(g.copy(u).multiplyScalar(m.y).addScaledVector(f,-d.y).multiplyScalar(L),p.copy(f).multiplyScalar(d.x).addScaledVector(u,-m.x).multiplyScalar(L),o[x].add(g),o[w].add(g),o[R].add(g),l[x].add(p),l[w].add(p),l[R].add(p))}let M=this.groups;M.length===0&&(M=[{start:0,count:e.count}]);for(let x=0,w=M.length;x<w;++x){const R=M[x],L=R.start,A=R.count;for(let U=L,P=L+A;U<P;U+=3)_(e.getX(U+0),e.getX(U+1),e.getX(U+2))}const y=new X,v=new X,S=new X,b=new X;function E(x){S.fromBufferAttribute(i,x),b.copy(S);const w=o[x];y.copy(w),y.sub(S.multiplyScalar(S.dot(w))).normalize(),v.crossVectors(b,w);const L=v.dot(l[x])<0?-1:1;a.setXYZW(x,y.x,y.y,y.z,L)}for(let x=0,w=M.length;x<w;++x){const R=M[x],L=R.start,A=R.count;for(let U=L,P=L+A;U<P;U+=3)E(e.getX(U+0)),E(e.getX(U+1)),E(e.getX(U+2))}}computeVertexNormals(){const e=this.index,t=this.getAttribute("position");if(t!==void 0){let r=this.getAttribute("normal");if(r===void 0)r=new kt(new Float32Array(t.count*3),3),this.setAttribute("normal",r);else for(let h=0,d=r.count;h<d;h++)r.setXYZ(h,0,0,0);const i=new X,s=new X,a=new X,o=new X,l=new X,c=new X,u=new X,f=new X;if(e)for(let h=0,d=e.count;h<d;h+=3){const m=e.getX(h+0),g=e.getX(h+1),p=e.getX(h+2);i.fromBufferAttribute(t,m),s.fromBufferAttribute(t,g),a.fromBufferAttribute(t,p),u.subVectors(a,s),f.subVectors(i,s),u.cross(f),o.fromBufferAttribute(r,m),l.fromBufferAttribute(r,g),c.fromBufferAttribute(r,p),o.add(u),l.add(u),c.add(u),r.setXYZ(m,o.x,o.y,o.z),r.setXYZ(g,l.x,l.y,l.z),r.setXYZ(p,c.x,c.y,c.z)}else for(let h=0,d=t.count;h<d;h+=3)i.fromBufferAttribute(t,h+0),s.fromBufferAttribute(t,h+1),a.fromBufferAttribute(t,h+2),u.subVectors(a,s),f.subVectors(i,s),u.cross(f),r.setXYZ(h+0,u.x,u.y,u.z),r.setXYZ(h+1,u.x,u.y,u.z),r.setXYZ(h+2,u.x,u.y,u.z);this.normalizeNormals(),r.needsUpdate=!0}}normalizeNormals(){const e=this.attributes.normal;for(let t=0,r=e.count;t<r;t++)nn.fromBufferAttribute(e,t),nn.normalize(),e.setXYZ(t,nn.x,nn.y,nn.z)}toNonIndexed(){function e(o,l){const c=o.array,u=o.itemSize,f=o.normalized,h=new c.constructor(l.length*u);let d=0,m=0;for(let g=0,p=l.length;g<p;g++){o.isInterleavedBufferAttribute?d=l[g]*o.data.stride+o.offset:d=l[g]*u;for(let _=0;_<u;_++)h[m++]=c[d++]}return new kt(h,u,f)}if(this.index===null)return $e("BufferGeometry.toNonIndexed(): BufferGeometry is already non-indexed."),this;const t=new Dt,r=this.index.array,i=this.attributes;for(const o in i){const l=i[o],c=e(l,r);t.setAttribute(o,c)}const s=this.morphAttributes;for(const o in s){const l=[],c=s[o];for(let u=0,f=c.length;u<f;u++){const h=c[u],d=e(h,r);l.push(d)}t.morphAttributes[o]=l}t.morphTargetsRelative=this.morphTargetsRelative;const a=this.groups;for(let o=0,l=a.length;o<l;o++){const c=a[o];t.addGroup(c.start,c.count,c.materialIndex)}return t}toJSON(){const e={metadata:{version:4.7,type:"BufferGeometry",generator:"BufferGeometry.toJSON"}};if(e.uuid=this.uuid,e.type=this.type,this.name!==""&&(e.name=this.name),Object.keys(this.userData).length>0&&(e.userData=this.userData),this.parameters!==void 0){const l=this.parameters;for(const c in l)l[c]!==void 0&&(e[c]=l[c]);return e}e.data={attributes:{}};const t=this.index;t!==null&&(e.data.index={type:t.array.constructor.name,array:Array.prototype.slice.call(t.array)});const r=this.attributes;for(const l in r){const c=r[l];e.data.attributes[l]=c.toJSON(e.data)}const i={};let s=!1;for(const l in this.morphAttributes){const c=this.morphAttributes[l],u=[];for(let f=0,h=c.length;f<h;f++){const d=c[f];u.push(d.toJSON(e.data))}u.length>0&&(i[l]=u,s=!0)}s&&(e.data.morphAttributes=i,e.data.morphTargetsRelative=this.morphTargetsRelative);const a=this.groups;a.length>0&&(e.data.groups=JSON.parse(JSON.stringify(a)));const o=this.boundingSphere;return o!==null&&(e.data.boundingSphere=o.toJSON()),e}clone(){return new this.constructor().copy(this)}copy(e){this.index=null,this.attributes={},this.morphAttributes={},this.groups=[],this.boundingBox=null,this.boundingSphere=null;const t={};this.name=e.name;const r=e.index;r!==null&&this.setIndex(r.clone());const i=e.attributes;for(const c in i){const u=i[c];this.setAttribute(c,u.clone(t))}const s=e.morphAttributes;for(const c in s){const u=[],f=s[c];for(let h=0,d=f.length;h<d;h++)u.push(f[h].clone(t));this.morphAttributes[c]=u}this.morphTargetsRelative=e.morphTargetsRelative;const a=e.groups;for(let c=0,u=a.length;c<u;c++){const f=a[c];this.addGroup(f.start,f.count,f.materialIndex)}const o=e.boundingBox;o!==null&&(this.boundingBox=o.clone());const l=e.boundingSphere;return l!==null&&(this.boundingSphere=l.clone()),this.drawRange.start=e.drawRange.start,this.drawRange.count=e.drawRange.count,this.userData=e.userData,this}dispose(){this.dispatchEvent({type:"dispose"})}}class H_{constructor(e,t){this.isInterleavedBuffer=!0,this.array=e,this.stride=t,this.count=e!==void 0?e.length/t:0,this.usage=oh,this.updateRanges=[],this.version=0,this.uuid=pr()}onUploadCallback(){}set needsUpdate(e){e===!0&&this.version++}setUsage(e){return this.usage=e,this}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}copy(e){return this.array=new e.array.constructor(e.array),this.count=e.count,this.stride=e.stride,this.usage=e.usage,this}copyAt(e,t,r){e*=this.stride,r*=t.stride;for(let i=0,s=this.stride;i<s;i++)this.array[e+i]=t.array[r+i];return this}set(e,t=0){return this.array.set(e,t),this}clone(e){e.arrayBuffers===void 0&&(e.arrayBuffers={}),this.array.buffer._uuid===void 0&&(this.array.buffer._uuid=pr()),e.arrayBuffers[this.array.buffer._uuid]===void 0&&(e.arrayBuffers[this.array.buffer._uuid]=this.array.slice(0).buffer);const t=new this.array.constructor(e.arrayBuffers[this.array.buffer._uuid]),r=new this.constructor(t,this.stride);return r.setUsage(this.usage),r}onUpload(e){return this.onUploadCallback=e,this}toJSON(e){return e.arrayBuffers===void 0&&(e.arrayBuffers={}),this.array.buffer._uuid===void 0&&(this.array.buffer._uuid=pr()),e.arrayBuffers[this.array.buffer._uuid]===void 0&&(e.arrayBuffers[this.array.buffer._uuid]=Array.from(new Uint32Array(this.array.buffer))),{uuid:this.uuid,buffer:this.array.buffer._uuid,type:this.array.constructor.name,stride:this.stride}}}const xn=new X;class ul{constructor(e,t,r,i=!1){this.isInterleavedBufferAttribute=!0,this.name="",this.data=e,this.itemSize=t,this.offset=r,this.normalized=i}get count(){return this.data.count}get array(){return this.data.array}set needsUpdate(e){this.data.needsUpdate=e}applyMatrix4(e){for(let t=0,r=this.data.count;t<r;t++)xn.fromBufferAttribute(this,t),xn.applyMatrix4(e),this.setXYZ(t,xn.x,xn.y,xn.z);return this}applyNormalMatrix(e){for(let t=0,r=this.count;t<r;t++)xn.fromBufferAttribute(this,t),xn.applyNormalMatrix(e),this.setXYZ(t,xn.x,xn.y,xn.z);return this}transformDirection(e){for(let t=0,r=this.count;t<r;t++)xn.fromBufferAttribute(this,t),xn.transformDirection(e),this.setXYZ(t,xn.x,xn.y,xn.z);return this}getComponent(e,t){let r=this.array[e*this.data.stride+this.offset+t];return this.normalized&&(r=Ti(r,this.array)),r}setComponent(e,t,r){return this.normalized&&(r=Mt(r,this.array)),this.data.array[e*this.data.stride+this.offset+t]=r,this}setX(e,t){return this.normalized&&(t=Mt(t,this.array)),this.data.array[e*this.data.stride+this.offset]=t,this}setY(e,t){return this.normalized&&(t=Mt(t,this.array)),this.data.array[e*this.data.stride+this.offset+1]=t,this}setZ(e,t){return this.normalized&&(t=Mt(t,this.array)),this.data.array[e*this.data.stride+this.offset+2]=t,this}setW(e,t){return this.normalized&&(t=Mt(t,this.array)),this.data.array[e*this.data.stride+this.offset+3]=t,this}getX(e){let t=this.data.array[e*this.data.stride+this.offset];return this.normalized&&(t=Ti(t,this.array)),t}getY(e){let t=this.data.array[e*this.data.stride+this.offset+1];return this.normalized&&(t=Ti(t,this.array)),t}getZ(e){let t=this.data.array[e*this.data.stride+this.offset+2];return this.normalized&&(t=Ti(t,this.array)),t}getW(e){let t=this.data.array[e*this.data.stride+this.offset+3];return this.normalized&&(t=Ti(t,this.array)),t}setXY(e,t,r){return e=e*this.data.stride+this.offset,this.normalized&&(t=Mt(t,this.array),r=Mt(r,this.array)),this.data.array[e+0]=t,this.data.array[e+1]=r,this}setXYZ(e,t,r,i){return e=e*this.data.stride+this.offset,this.normalized&&(t=Mt(t,this.array),r=Mt(r,this.array),i=Mt(i,this.array)),this.data.array[e+0]=t,this.data.array[e+1]=r,this.data.array[e+2]=i,this}setXYZW(e,t,r,i,s){return e=e*this.data.stride+this.offset,this.normalized&&(t=Mt(t,this.array),r=Mt(r,this.array),i=Mt(i,this.array),s=Mt(s,this.array)),this.data.array[e+0]=t,this.data.array[e+1]=r,this.data.array[e+2]=i,this.data.array[e+3]=s,this}clone(e){if(e===void 0){cl("InterleavedBufferAttribute.clone(): Cloning an interleaved buffer attribute will de-interleave buffer data.");const t=[];for(let r=0;r<this.count;r++){const i=r*this.data.stride+this.offset;for(let s=0;s<this.itemSize;s++)t.push(this.data.array[i+s])}return new kt(new this.array.constructor(t),this.itemSize,this.normalized)}else return e.interleavedBuffers===void 0&&(e.interleavedBuffers={}),e.interleavedBuffers[this.data.uuid]===void 0&&(e.interleavedBuffers[this.data.uuid]=this.data.clone(e)),new ul(e.interleavedBuffers[this.data.uuid],this.itemSize,this.offset,this.normalized)}toJSON(e){if(e===void 0){cl("InterleavedBufferAttribute.toJSON(): Serializing an interleaved buffer attribute will de-interleave buffer data.");const t=[];for(let r=0;r<this.count;r++){const i=r*this.data.stride+this.offset;for(let s=0;s<this.itemSize;s++)t.push(this.data.array[i+s])}return{itemSize:this.itemSize,type:this.array.constructor.name,array:t,normalized:this.normalized}}else return e.interleavedBuffers===void 0&&(e.interleavedBuffers={}),e.interleavedBuffers[this.data.uuid]===void 0&&(e.interleavedBuffers[this.data.uuid]=this.data.toJSON(e)),{isInterleavedBufferAttribute:!0,itemSize:this.itemSize,data:this.data.uuid,offset:this.offset,normalized:this.normalized}}}let V_=0;class Zi extends hi{constructor(){super(),this.isMaterial=!0,Object.defineProperty(this,"id",{value:V_++}),this.uuid=pr(),this.name="",this.type="Material",this.blending=zr,this.side=Xi,this.vertexColors=!1,this.opacity=1,this.transparent=!1,this.alphaHash=!1,this.blendSrc=Su,this.blendDst=bu,this.blendEquation=Nr,this.blendSrcAlpha=null,this.blendDstAlpha=null,this.blendEquationAlpha=null,this.blendColor=new lt(0,0,0),this.blendAlpha=0,this.depthFunc=Ns,this.depthTest=!0,this.depthWrite=!0,this.stencilWriteMask=255,this.stencilFunc=Jf,this.stencilRef=0,this.stencilFuncMask=255,this.stencilFail=as,this.stencilZFail=as,this.stencilZPass=as,this.stencilWrite=!1,this.clippingPlanes=null,this.clipIntersection=!1,this.clipShadows=!1,this.shadowSide=null,this.colorWrite=!0,this.precision=null,this.polygonOffset=!1,this.polygonOffsetFactor=0,this.polygonOffsetUnits=0,this.dithering=!1,this.alphaToCoverage=!1,this.premultipliedAlpha=!1,this.forceSinglePass=!1,this.allowOverride=!0,this.visible=!0,this.toneMapped=!0,this.userData={},this.version=0,this._alphaTest=0}get alphaTest(){return this._alphaTest}set alphaTest(e){this._alphaTest>0!=e>0&&this.version++,this._alphaTest=e}onBeforeRender(){}onBeforeCompile(){}customProgramCacheKey(){return this.onBeforeCompile.toString()}setValues(e){if(e!==void 0)for(const t in e){const r=e[t];if(r===void 0){$e(`Material: parameter '${t}' has value of undefined.`);continue}const i=this[t];if(i===void 0){$e(`Material: '${t}' is not a property of THREE.${this.type}.`);continue}i&&i.isColor?i.set(r):i&&i.isVector3&&r&&r.isVector3?i.copy(r):this[t]=r}}toJSON(e){const t=e===void 0||typeof e=="string";t&&(e={textures:{},images:{}});const r={metadata:{version:4.7,type:"Material",generator:"Material.toJSON"}};r.uuid=this.uuid,r.type=this.type,this.name!==""&&(r.name=this.name),this.color&&this.color.isColor&&(r.color=this.color.getHex()),this.roughness!==void 0&&(r.roughness=this.roughness),this.metalness!==void 0&&(r.metalness=this.metalness),this.sheen!==void 0&&(r.sheen=this.sheen),this.sheenColor&&this.sheenColor.isColor&&(r.sheenColor=this.sheenColor.getHex()),this.sheenRoughness!==void 0&&(r.sheenRoughness=this.sheenRoughness),this.emissive&&this.emissive.isColor&&(r.emissive=this.emissive.getHex()),this.emissiveIntensity!==void 0&&this.emissiveIntensity!==1&&(r.emissiveIntensity=this.emissiveIntensity),this.specular&&this.specular.isColor&&(r.specular=this.specular.getHex()),this.specularIntensity!==void 0&&(r.specularIntensity=this.specularIntensity),this.specularColor&&this.specularColor.isColor&&(r.specularColor=this.specularColor.getHex()),this.shininess!==void 0&&(r.shininess=this.shininess),this.clearcoat!==void 0&&(r.clearcoat=this.clearcoat),this.clearcoatRoughness!==void 0&&(r.clearcoatRoughness=this.clearcoatRoughness),this.clearcoatMap&&this.clearcoatMap.isTexture&&(r.clearcoatMap=this.clearcoatMap.toJSON(e).uuid),this.clearcoatRoughnessMap&&this.clearcoatRoughnessMap.isTexture&&(r.clearcoatRoughnessMap=this.clearcoatRoughnessMap.toJSON(e).uuid),this.clearcoatNormalMap&&this.clearcoatNormalMap.isTexture&&(r.clearcoatNormalMap=this.clearcoatNormalMap.toJSON(e).uuid,r.clearcoatNormalScale=this.clearcoatNormalScale.toArray()),this.sheenColorMap&&this.sheenColorMap.isTexture&&(r.sheenColorMap=this.sheenColorMap.toJSON(e).uuid),this.sheenRoughnessMap&&this.sheenRoughnessMap.isTexture&&(r.sheenRoughnessMap=this.sheenRoughnessMap.toJSON(e).uuid),this.dispersion!==void 0&&(r.dispersion=this.dispersion),this.iridescence!==void 0&&(r.iridescence=this.iridescence),this.iridescenceIOR!==void 0&&(r.iridescenceIOR=this.iridescenceIOR),this.iridescenceThicknessRange!==void 0&&(r.iridescenceThicknessRange=this.iridescenceThicknessRange),this.iridescenceMap&&this.iridescenceMap.isTexture&&(r.iridescenceMap=this.iridescenceMap.toJSON(e).uuid),this.iridescenceThicknessMap&&this.iridescenceThicknessMap.isTexture&&(r.iridescenceThicknessMap=this.iridescenceThicknessMap.toJSON(e).uuid),this.anisotropy!==void 0&&(r.anisotropy=this.anisotropy),this.anisotropyRotation!==void 0&&(r.anisotropyRotation=this.anisotropyRotation),this.anisotropyMap&&this.anisotropyMap.isTexture&&(r.anisotropyMap=this.anisotropyMap.toJSON(e).uuid),this.map&&this.map.isTexture&&(r.map=this.map.toJSON(e).uuid),this.matcap&&this.matcap.isTexture&&(r.matcap=this.matcap.toJSON(e).uuid),this.alphaMap&&this.alphaMap.isTexture&&(r.alphaMap=this.alphaMap.toJSON(e).uuid),this.lightMap&&this.lightMap.isTexture&&(r.lightMap=this.lightMap.toJSON(e).uuid,r.lightMapIntensity=this.lightMapIntensity),this.aoMap&&this.aoMap.isTexture&&(r.aoMap=this.aoMap.toJSON(e).uuid,r.aoMapIntensity=this.aoMapIntensity),this.bumpMap&&this.bumpMap.isTexture&&(r.bumpMap=this.bumpMap.toJSON(e).uuid,r.bumpScale=this.bumpScale),this.normalMap&&this.normalMap.isTexture&&(r.normalMap=this.normalMap.toJSON(e).uuid,r.normalMapType=this.normalMapType,r.normalScale=this.normalScale.toArray()),this.displacementMap&&this.displacementMap.isTexture&&(r.displacementMap=this.displacementMap.toJSON(e).uuid,r.displacementScale=this.displacementScale,r.displacementBias=this.displacementBias),this.roughnessMap&&this.roughnessMap.isTexture&&(r.roughnessMap=this.roughnessMap.toJSON(e).uuid),this.metalnessMap&&this.metalnessMap.isTexture&&(r.metalnessMap=this.metalnessMap.toJSON(e).uuid),this.emissiveMap&&this.emissiveMap.isTexture&&(r.emissiveMap=this.emissiveMap.toJSON(e).uuid),this.specularMap&&this.specularMap.isTexture&&(r.specularMap=this.specularMap.toJSON(e).uuid),this.specularIntensityMap&&this.specularIntensityMap.isTexture&&(r.specularIntensityMap=this.specularIntensityMap.toJSON(e).uuid),this.specularColorMap&&this.specularColorMap.isTexture&&(r.specularColorMap=this.specularColorMap.toJSON(e).uuid),this.envMap&&this.envMap.isTexture&&(r.envMap=this.envMap.toJSON(e).uuid,this.combine!==void 0&&(r.combine=this.combine)),this.envMapRotation!==void 0&&(r.envMapRotation=this.envMapRotation.toArray()),this.envMapIntensity!==void 0&&(r.envMapIntensity=this.envMapIntensity),this.reflectivity!==void 0&&(r.reflectivity=this.reflectivity),this.refractionRatio!==void 0&&(r.refractionRatio=this.refractionRatio),this.gradientMap&&this.gradientMap.isTexture&&(r.gradientMap=this.gradientMap.toJSON(e).uuid),this.transmission!==void 0&&(r.transmission=this.transmission),this.transmissionMap&&this.transmissionMap.isTexture&&(r.transmissionMap=this.transmissionMap.toJSON(e).uuid),this.thickness!==void 0&&(r.thickness=this.thickness),this.thicknessMap&&this.thicknessMap.isTexture&&(r.thicknessMap=this.thicknessMap.toJSON(e).uuid),this.attenuationDistance!==void 0&&this.attenuationDistance!==1/0&&(r.attenuationDistance=this.attenuationDistance),this.attenuationColor!==void 0&&(r.attenuationColor=this.attenuationColor.getHex()),this.size!==void 0&&(r.size=this.size),this.shadowSide!==null&&(r.shadowSide=this.shadowSide),this.sizeAttenuation!==void 0&&(r.sizeAttenuation=this.sizeAttenuation),this.blending!==zr&&(r.blending=this.blending),this.side!==Xi&&(r.side=this.side),this.vertexColors===!0&&(r.vertexColors=!0),this.opacity<1&&(r.opacity=this.opacity),this.transparent===!0&&(r.transparent=!0),this.blendSrc!==Su&&(r.blendSrc=this.blendSrc),this.blendDst!==bu&&(r.blendDst=this.blendDst),this.blendEquation!==Nr&&(r.blendEquation=this.blendEquation),this.blendSrcAlpha!==null&&(r.blendSrcAlpha=this.blendSrcAlpha),this.blendDstAlpha!==null&&(r.blendDstAlpha=this.blendDstAlpha),this.blendEquationAlpha!==null&&(r.blendEquationAlpha=this.blendEquationAlpha),this.blendColor&&this.blendColor.isColor&&(r.blendColor=this.blendColor.getHex()),this.blendAlpha!==0&&(r.blendAlpha=this.blendAlpha),this.depthFunc!==Ns&&(r.depthFunc=this.depthFunc),this.depthTest===!1&&(r.depthTest=this.depthTest),this.depthWrite===!1&&(r.depthWrite=this.depthWrite),this.colorWrite===!1&&(r.colorWrite=this.colorWrite),this.stencilWriteMask!==255&&(r.stencilWriteMask=this.stencilWriteMask),this.stencilFunc!==Jf&&(r.stencilFunc=this.stencilFunc),this.stencilRef!==0&&(r.stencilRef=this.stencilRef),this.stencilFuncMask!==255&&(r.stencilFuncMask=this.stencilFuncMask),this.stencilFail!==as&&(r.stencilFail=this.stencilFail),this.stencilZFail!==as&&(r.stencilZFail=this.stencilZFail),this.stencilZPass!==as&&(r.stencilZPass=this.stencilZPass),this.stencilWrite===!0&&(r.stencilWrite=this.stencilWrite),this.rotation!==void 0&&this.rotation!==0&&(r.rotation=this.rotation),this.polygonOffset===!0&&(r.polygonOffset=!0),this.polygonOffsetFactor!==0&&(r.polygonOffsetFactor=this.polygonOffsetFactor),this.polygonOffsetUnits!==0&&(r.polygonOffsetUnits=this.polygonOffsetUnits),this.linewidth!==void 0&&this.linewidth!==1&&(r.linewidth=this.linewidth),this.dashSize!==void 0&&(r.dashSize=this.dashSize),this.gapSize!==void 0&&(r.gapSize=this.gapSize),this.scale!==void 0&&(r.scale=this.scale),this.dithering===!0&&(r.dithering=!0),this.alphaTest>0&&(r.alphaTest=this.alphaTest),this.alphaHash===!0&&(r.alphaHash=!0),this.alphaToCoverage===!0&&(r.alphaToCoverage=!0),this.premultipliedAlpha===!0&&(r.premultipliedAlpha=!0),this.forceSinglePass===!0&&(r.forceSinglePass=!0),this.allowOverride===!1&&(r.allowOverride=!1),this.wireframe===!0&&(r.wireframe=!0),this.wireframeLinewidth>1&&(r.wireframeLinewidth=this.wireframeLinewidth),this.wireframeLinecap!=="round"&&(r.wireframeLinecap=this.wireframeLinecap),this.wireframeLinejoin!=="round"&&(r.wireframeLinejoin=this.wireframeLinejoin),this.flatShading===!0&&(r.flatShading=!0),this.visible===!1&&(r.visible=!1),this.toneMapped===!1&&(r.toneMapped=!1),this.fog===!1&&(r.fog=!1),Object.keys(this.userData).length>0&&(r.userData=this.userData);function i(s){const a=[];for(const o in s){const l=s[o];delete l.metadata,a.push(l)}return a}if(t){const s=i(e.textures),a=i(e.images);s.length>0&&(r.textures=s),a.length>0&&(r.images=a)}return r}clone(){return new this.constructor().copy(this)}copy(e){this.name=e.name,this.blending=e.blending,this.side=e.side,this.vertexColors=e.vertexColors,this.opacity=e.opacity,this.transparent=e.transparent,this.blendSrc=e.blendSrc,this.blendDst=e.blendDst,this.blendEquation=e.blendEquation,this.blendSrcAlpha=e.blendSrcAlpha,this.blendDstAlpha=e.blendDstAlpha,this.blendEquationAlpha=e.blendEquationAlpha,this.blendColor.copy(e.blendColor),this.blendAlpha=e.blendAlpha,this.depthFunc=e.depthFunc,this.depthTest=e.depthTest,this.depthWrite=e.depthWrite,this.stencilWriteMask=e.stencilWriteMask,this.stencilFunc=e.stencilFunc,this.stencilRef=e.stencilRef,this.stencilFuncMask=e.stencilFuncMask,this.stencilFail=e.stencilFail,this.stencilZFail=e.stencilZFail,this.stencilZPass=e.stencilZPass,this.stencilWrite=e.stencilWrite;const t=e.clippingPlanes;let r=null;if(t!==null){const i=t.length;r=new Array(i);for(let s=0;s!==i;++s)r[s]=t[s].clone()}return this.clippingPlanes=r,this.clipIntersection=e.clipIntersection,this.clipShadows=e.clipShadows,this.shadowSide=e.shadowSide,this.colorWrite=e.colorWrite,this.precision=e.precision,this.polygonOffset=e.polygonOffset,this.polygonOffsetFactor=e.polygonOffsetFactor,this.polygonOffsetUnits=e.polygonOffsetUnits,this.dithering=e.dithering,this.alphaTest=e.alphaTest,this.alphaHash=e.alphaHash,this.alphaToCoverage=e.alphaToCoverage,this.premultipliedAlpha=e.premultipliedAlpha,this.forceSinglePass=e.forceSinglePass,this.allowOverride=e.allowOverride,this.visible=e.visible,this.toneMapped=e.toneMapped,this.userData=JSON.parse(JSON.stringify(e.userData)),this}dispose(){this.dispatchEvent({type:"dispose"})}set needsUpdate(e){e===!0&&this.version++}}class Ko extends Zi{constructor(e){super(),this.isSpriteMaterial=!0,this.type="SpriteMaterial",this.color=new lt(16777215),this.map=null,this.alphaMap=null,this.rotation=0,this.sizeAttenuation=!0,this.transparent=!0,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.alphaMap=e.alphaMap,this.rotation=e.rotation,this.sizeAttenuation=e.sizeAttenuation,this.fog=e.fog,this}}let _s;const pa=new X,vs=new X,xs=new X,Ms=new We,ma=new We,Um=new Ot,po=new X,ga=new X,mo=new X,fd=new We,bc=new We,dd=new We;class yc extends mn{constructor(e=new Ko){if(super(),this.isSprite=!0,this.type="Sprite",_s===void 0){_s=new Dt;const t=new Float32Array([-.5,-.5,0,0,0,.5,-.5,0,1,0,.5,.5,0,1,1,-.5,.5,0,0,1]),r=new H_(t,5);_s.setIndex([0,1,2,0,2,3]),_s.setAttribute("position",new ul(r,3,0,!1)),_s.setAttribute("uv",new ul(r,2,3,!1))}this.geometry=_s,this.material=e,this.center=new We(.5,.5),this.count=1}raycast(e,t){e.camera===null&&ft('Sprite: "Raycaster.camera" needs to be set in order to raycast against sprites.'),vs.setFromMatrixScale(this.matrixWorld),Um.copy(e.camera.matrixWorld),this.modelViewMatrix.multiplyMatrices(e.camera.matrixWorldInverse,this.matrixWorld),xs.setFromMatrixPosition(this.modelViewMatrix),e.camera.isPerspectiveCamera&&this.material.sizeAttenuation===!1&&vs.multiplyScalar(-xs.z);const r=this.material.rotation;let i,s;r!==0&&(s=Math.cos(r),i=Math.sin(r));const a=this.center;go(po.set(-.5,-.5,0),xs,a,vs,i,s),go(ga.set(.5,-.5,0),xs,a,vs,i,s),go(mo.set(.5,.5,0),xs,a,vs,i,s),fd.set(0,0),bc.set(1,0),dd.set(1,1);let o=e.ray.intersectTriangle(po,ga,mo,!1,pa);if(o===null&&(go(ga.set(-.5,.5,0),xs,a,vs,i,s),bc.set(0,1),o=e.ray.intersectTriangle(po,mo,ga,!1,pa),o===null))return;const l=e.ray.origin.distanceTo(pa);l<e.near||l>e.far||t.push({distance:l,point:pa.clone(),uv:$n.getInterpolation(pa,po,ga,mo,fd,bc,dd,new We),face:null,object:this})}copy(e,t){return super.copy(e,t),e.center!==void 0&&this.center.copy(e.center),this.material=e.material,this}}function go(n,e,t,r,i,s){Ms.subVectors(n,t).addScalar(.5).multiply(r),i!==void 0?(ma.x=s*Ms.x-i*Ms.y,ma.y=i*Ms.x+s*Ms.y):ma.copy(Ms),n.copy(e),n.x+=ma.x,n.y+=ma.y,n.applyMatrix4(Um)}const ki=new X,Tc=new X,_o=new X,sr=new X,Ec=new X,vo=new X,wc=new X;class Rl{constructor(e=new X,t=new X(0,0,-1)){this.origin=e,this.direction=t}set(e,t){return this.origin.copy(e),this.direction.copy(t),this}copy(e){return this.origin.copy(e.origin),this.direction.copy(e.direction),this}at(e,t){return t.copy(this.origin).addScaledVector(this.direction,e)}lookAt(e){return this.direction.copy(e).sub(this.origin).normalize(),this}recast(e){return this.origin.copy(this.at(e,ki)),this}closestPointToPoint(e,t){t.subVectors(e,this.origin);const r=t.dot(this.direction);return r<0?t.copy(this.origin):t.copy(this.origin).addScaledVector(this.direction,r)}distanceToPoint(e){return Math.sqrt(this.distanceSqToPoint(e))}distanceSqToPoint(e){const t=ki.subVectors(e,this.origin).dot(this.direction);return t<0?this.origin.distanceToSquared(e):(ki.copy(this.origin).addScaledVector(this.direction,t),ki.distanceToSquared(e))}distanceSqToSegment(e,t,r,i){Tc.copy(e).add(t).multiplyScalar(.5),_o.copy(t).sub(e).normalize(),sr.copy(this.origin).sub(Tc);const s=e.distanceTo(t)*.5,a=-this.direction.dot(_o),o=sr.dot(this.direction),l=-sr.dot(_o),c=sr.lengthSq(),u=Math.abs(1-a*a);let f,h,d,m;if(u>0)if(f=a*l-o,h=a*o-l,m=s*u,f>=0)if(h>=-m)if(h<=m){const g=1/u;f*=g,h*=g,d=f*(f+a*h+2*o)+h*(a*f+h+2*l)+c}else h=s,f=Math.max(0,-(a*h+o)),d=-f*f+h*(h+2*l)+c;else h=-s,f=Math.max(0,-(a*h+o)),d=-f*f+h*(h+2*l)+c;else h<=-m?(f=Math.max(0,-(-a*s+o)),h=f>0?-s:Math.min(Math.max(-s,-l),s),d=-f*f+h*(h+2*l)+c):h<=m?(f=0,h=Math.min(Math.max(-s,-l),s),d=h*(h+2*l)+c):(f=Math.max(0,-(a*s+o)),h=f>0?s:Math.min(Math.max(-s,-l),s),d=-f*f+h*(h+2*l)+c);else h=a>0?-s:s,f=Math.max(0,-(a*h+o)),d=-f*f+h*(h+2*l)+c;return r&&r.copy(this.origin).addScaledVector(this.direction,f),i&&i.copy(Tc).addScaledVector(_o,h),d}intersectSphere(e,t){ki.subVectors(e.center,this.origin);const r=ki.dot(this.direction),i=ki.dot(ki)-r*r,s=e.radius*e.radius;if(i>s)return null;const a=Math.sqrt(s-i),o=r-a,l=r+a;return l<0?null:o<0?this.at(l,t):this.at(o,t)}intersectsSphere(e){return e.radius<0?!1:this.distanceSqToPoint(e.center)<=e.radius*e.radius}distanceToPlane(e){const t=e.normal.dot(this.direction);if(t===0)return e.distanceToPoint(this.origin)===0?0:null;const r=-(this.origin.dot(e.normal)+e.constant)/t;return r>=0?r:null}intersectPlane(e,t){const r=this.distanceToPlane(e);return r===null?null:this.at(r,t)}intersectsPlane(e){const t=e.distanceToPoint(this.origin);return t===0||e.normal.dot(this.direction)*t<0}intersectBox(e,t){let r,i,s,a,o,l;const c=1/this.direction.x,u=1/this.direction.y,f=1/this.direction.z,h=this.origin;return c>=0?(r=(e.min.x-h.x)*c,i=(e.max.x-h.x)*c):(r=(e.max.x-h.x)*c,i=(e.min.x-h.x)*c),u>=0?(s=(e.min.y-h.y)*u,a=(e.max.y-h.y)*u):(s=(e.max.y-h.y)*u,a=(e.min.y-h.y)*u),r>a||s>i||((s>r||isNaN(r))&&(r=s),(a<i||isNaN(i))&&(i=a),f>=0?(o=(e.min.z-h.z)*f,l=(e.max.z-h.z)*f):(o=(e.max.z-h.z)*f,l=(e.min.z-h.z)*f),r>l||o>i)||((o>r||r!==r)&&(r=o),(l<i||i!==i)&&(i=l),i<0)?null:this.at(r>=0?r:i,t)}intersectsBox(e){return this.intersectBox(e,ki)!==null}intersectTriangle(e,t,r,i,s){Ec.subVectors(t,e),vo.subVectors(r,e),wc.crossVectors(Ec,vo);let a=this.direction.dot(wc),o;if(a>0){if(i)return null;o=1}else if(a<0)o=-1,a=-a;else return null;sr.subVectors(this.origin,e);const l=o*this.direction.dot(vo.crossVectors(sr,vo));if(l<0)return null;const c=o*this.direction.dot(Ec.cross(sr));if(c<0||l+c>a)return null;const u=-o*sr.dot(wc);return u<0?null:this.at(u/a,s)}applyMatrix4(e){return this.origin.applyMatrix4(e),this.direction.transformDirection(e),this}equals(e){return e.origin.equals(this.origin)&&e.direction.equals(this.direction)}clone(){return new this.constructor().copy(this)}}class $h extends Zi{constructor(e){super(),this.isMeshBasicMaterial=!0,this.type="MeshBasicMaterial",this.color=new lt(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new Zr,this.combine=um,this.reflectivity=1,this.refractionRatio=.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.specularMap=e.specularMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.combine=e.combine,this.reflectivity=e.reflectivity,this.refractionRatio=e.refractionRatio,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.fog=e.fog,this}}const pd=new Ot,Rr=new Rl,xo=new js,md=new X,Mo=new X,So=new X,bo=new X,Ac=new X,yo=new X,gd=new X,To=new X;class Wn extends mn{constructor(e=new Dt,t=new $h){super(),this.isMesh=!0,this.type="Mesh",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.count=1,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),e.morphTargetInfluences!==void 0&&(this.morphTargetInfluences=e.morphTargetInfluences.slice()),e.morphTargetDictionary!==void 0&&(this.morphTargetDictionary=Object.assign({},e.morphTargetDictionary)),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}updateMorphTargets(){const t=this.geometry.morphAttributes,r=Object.keys(t);if(r.length>0){const i=t[r[0]];if(i!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let s=0,a=i.length;s<a;s++){const o=i[s].name||String(s);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=s}}}}getVertexPosition(e,t){const r=this.geometry,i=r.attributes.position,s=r.morphAttributes.position,a=r.morphTargetsRelative;t.fromBufferAttribute(i,e);const o=this.morphTargetInfluences;if(s&&o){yo.set(0,0,0);for(let l=0,c=s.length;l<c;l++){const u=o[l],f=s[l];u!==0&&(Ac.fromBufferAttribute(f,e),a?yo.addScaledVector(Ac,u):yo.addScaledVector(Ac.sub(t),u))}t.add(yo)}return t}raycast(e,t){const r=this.geometry,i=this.material,s=this.matrixWorld;i!==void 0&&(r.boundingSphere===null&&r.computeBoundingSphere(),xo.copy(r.boundingSphere),xo.applyMatrix4(s),Rr.copy(e.ray).recast(e.near),!(xo.containsPoint(Rr.origin)===!1&&(Rr.intersectSphere(xo,md)===null||Rr.origin.distanceToSquared(md)>(e.far-e.near)**2))&&(pd.copy(s).invert(),Rr.copy(e.ray).applyMatrix4(pd),!(r.boundingBox!==null&&Rr.intersectsBox(r.boundingBox)===!1)&&this._computeIntersections(e,t,Rr)))}_computeIntersections(e,t,r){let i;const s=this.geometry,a=this.material,o=s.index,l=s.attributes.position,c=s.attributes.uv,u=s.attributes.uv1,f=s.attributes.normal,h=s.groups,d=s.drawRange;if(o!==null)if(Array.isArray(a))for(let m=0,g=h.length;m<g;m++){const p=h[m],_=a[p.materialIndex],M=Math.max(p.start,d.start),y=Math.min(o.count,Math.min(p.start+p.count,d.start+d.count));for(let v=M,S=y;v<S;v+=3){const b=o.getX(v),E=o.getX(v+1),x=o.getX(v+2);i=Eo(this,_,e,r,c,u,f,b,E,x),i&&(i.faceIndex=Math.floor(v/3),i.face.materialIndex=p.materialIndex,t.push(i))}}else{const m=Math.max(0,d.start),g=Math.min(o.count,d.start+d.count);for(let p=m,_=g;p<_;p+=3){const M=o.getX(p),y=o.getX(p+1),v=o.getX(p+2);i=Eo(this,a,e,r,c,u,f,M,y,v),i&&(i.faceIndex=Math.floor(p/3),t.push(i))}}else if(l!==void 0)if(Array.isArray(a))for(let m=0,g=h.length;m<g;m++){const p=h[m],_=a[p.materialIndex],M=Math.max(p.start,d.start),y=Math.min(l.count,Math.min(p.start+p.count,d.start+d.count));for(let v=M,S=y;v<S;v+=3){const b=v,E=v+1,x=v+2;i=Eo(this,_,e,r,c,u,f,b,E,x),i&&(i.faceIndex=Math.floor(v/3),i.face.materialIndex=p.materialIndex,t.push(i))}}else{const m=Math.max(0,d.start),g=Math.min(l.count,d.start+d.count);for(let p=m,_=g;p<_;p+=3){const M=p,y=p+1,v=p+2;i=Eo(this,a,e,r,c,u,f,M,y,v),i&&(i.faceIndex=Math.floor(p/3),t.push(i))}}}}function W_(n,e,t,r,i,s,a,o){let l;if(e.side===sn?l=r.intersectTriangle(a,s,i,!0,o):l=r.intersectTriangle(i,s,a,e.side===Xi,o),l===null)return null;To.copy(o),To.applyMatrix4(n.matrixWorld);const c=t.ray.origin.distanceTo(To);return c<t.near||c>t.far?null:{distance:c,point:To.clone(),object:n}}function Eo(n,e,t,r,i,s,a,o,l,c){n.getVertexPosition(o,Mo),n.getVertexPosition(l,So),n.getVertexPosition(c,bo);const u=W_(n,e,t,r,Mo,So,bo,gd);if(u){const f=new X;$n.getBarycoord(gd,Mo,So,bo,f),i&&(u.uv=$n.getInterpolatedAttribute(i,o,l,c,f,new We)),s&&(u.uv1=$n.getInterpolatedAttribute(s,o,l,c,f,new We)),a&&(u.normal=$n.getInterpolatedAttribute(a,o,l,c,f,new X),u.normal.dot(r.direction)>0&&u.normal.multiplyScalar(-1));const h={a:o,b:l,c,normal:new X,materialIndex:0};$n.getNormal(Mo,So,bo,h.normal),u.face=h,u.barycoord=f}return u}class X_ extends Zt{constructor(e=null,t=1,r=1,i,s,a,o,l,c=cn,u=cn,f,h){super(null,a,o,l,c,u,i,s,f,h),this.isDataTexture=!0,this.image={data:e,width:t,height:r},this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}}class Y_ extends kt{constructor(e,t,r,i=1){super(e,t,r),this.isInstancedBufferAttribute=!0,this.meshPerAttribute=i}copy(e){return super.copy(e),this.meshPerAttribute=e.meshPerAttribute,this}toJSON(){const e=super.toJSON();return e.meshPerAttribute=this.meshPerAttribute,e.isInstancedBufferAttribute=!0,e}}const Rc=new X,q_=new X,j_=new nt;class lr{constructor(e=new X(1,0,0),t=0){this.isPlane=!0,this.normal=e,this.constant=t}set(e,t){return this.normal.copy(e),this.constant=t,this}setComponents(e,t,r,i){return this.normal.set(e,t,r),this.constant=i,this}setFromNormalAndCoplanarPoint(e,t){return this.normal.copy(e),this.constant=-t.dot(this.normal),this}setFromCoplanarPoints(e,t,r){const i=Rc.subVectors(r,t).cross(q_.subVectors(e,t)).normalize();return this.setFromNormalAndCoplanarPoint(i,e),this}copy(e){return this.normal.copy(e.normal),this.constant=e.constant,this}normalize(){const e=1/this.normal.length();return this.normal.multiplyScalar(e),this.constant*=e,this}negate(){return this.constant*=-1,this.normal.negate(),this}distanceToPoint(e){return this.normal.dot(e)+this.constant}distanceToSphere(e){return this.distanceToPoint(e.center)-e.radius}projectPoint(e,t){return t.copy(e).addScaledVector(this.normal,-this.distanceToPoint(e))}intersectLine(e,t,r=!0){const i=e.delta(Rc),s=this.normal.dot(i);if(s===0)return this.distanceToPoint(e.start)===0?t.copy(e.start):null;const a=-(e.start.dot(this.normal)+this.constant)/s;return r===!0&&(a<0||a>1)?null:t.copy(e.start).addScaledVector(i,a)}intersectsLine(e){const t=this.distanceToPoint(e.start),r=this.distanceToPoint(e.end);return t<0&&r>0||r<0&&t>0}intersectsBox(e){return e.intersectsPlane(this)}intersectsSphere(e){return e.intersectsPlane(this)}coplanarPoint(e){return e.copy(this.normal).multiplyScalar(-this.constant)}applyMatrix4(e,t){const r=t||j_.getNormalMatrix(e),i=this.coplanarPoint(Rc).applyMatrix4(e),s=this.normal.applyMatrix3(r).normalize();return this.constant=-i.dot(s),this}translate(e){return this.constant-=e.dot(this.normal),this}equals(e){return e.normal.equals(this.normal)&&e.constant===this.constant}clone(){return new this.constructor().copy(this)}}const Cr=new js,K_=new We(.5,.5),wo=new X;class Lm{constructor(e=new lr,t=new lr,r=new lr,i=new lr,s=new lr,a=new lr){this.planes=[e,t,r,i,s,a]}set(e,t,r,i,s,a){const o=this.planes;return o[0].copy(e),o[1].copy(t),o[2].copy(r),o[3].copy(i),o[4].copy(s),o[5].copy(a),this}copy(e){const t=this.planes;for(let r=0;r<6;r++)t[r].copy(e.planes[r]);return this}setFromProjectionMatrix(e,t=Ai,r=!1){const i=this.planes,s=e.elements,a=s[0],o=s[1],l=s[2],c=s[3],u=s[4],f=s[5],h=s[6],d=s[7],m=s[8],g=s[9],p=s[10],_=s[11],M=s[12],y=s[13],v=s[14],S=s[15];if(i[0].setComponents(c-a,d-u,_-m,S-M).normalize(),i[1].setComponents(c+a,d+u,_+m,S+M).normalize(),i[2].setComponents(c+o,d+f,_+g,S+y).normalize(),i[3].setComponents(c-o,d-f,_-g,S-y).normalize(),r)i[4].setComponents(l,h,p,v).normalize(),i[5].setComponents(c-l,d-h,_-p,S-v).normalize();else if(i[4].setComponents(c-l,d-h,_-p,S-v).normalize(),t===Ai)i[5].setComponents(c+l,d+h,_+p,S+v).normalize();else if(t===ol)i[5].setComponents(l,h,p,v).normalize();else throw new Error("THREE.Frustum.setFromProjectionMatrix(): Invalid coordinate system: "+t);return this}intersectsObject(e){if(e.boundingSphere!==void 0)e.boundingSphere===null&&e.computeBoundingSphere(),Cr.copy(e.boundingSphere).applyMatrix4(e.matrixWorld);else{const t=e.geometry;t.boundingSphere===null&&t.computeBoundingSphere(),Cr.copy(t.boundingSphere).applyMatrix4(e.matrixWorld)}return this.intersectsSphere(Cr)}intersectsSprite(e){Cr.center.set(0,0,0);const t=K_.distanceTo(e.center);return Cr.radius=.7071067811865476+t,Cr.applyMatrix4(e.matrixWorld),this.intersectsSphere(Cr)}intersectsSphere(e){const t=this.planes,r=e.center,i=-e.radius;for(let s=0;s<6;s++)if(t[s].distanceToPoint(r)<i)return!1;return!0}intersectsBox(e){const t=this.planes;for(let r=0;r<6;r++){const i=t[r];if(wo.x=i.normal.x>0?e.max.x:e.min.x,wo.y=i.normal.y>0?e.max.y:e.min.y,wo.z=i.normal.z>0?e.max.z:e.min.z,i.distanceToPoint(wo)<0)return!1}return!0}containsPoint(e){const t=this.planes;for(let r=0;r<6;r++)if(t[r].distanceToPoint(e)<0)return!1;return!0}clone(){return new this.constructor().copy(this)}}class hh extends Zi{constructor(e){super(),this.isLineBasicMaterial=!0,this.type="LineBasicMaterial",this.color=new lt(16777215),this.map=null,this.linewidth=1,this.linecap="round",this.linejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.linewidth=e.linewidth,this.linecap=e.linecap,this.linejoin=e.linejoin,this.fog=e.fog,this}}const hl=new X,fl=new X,_d=new Ot,_a=new Rl,Ao=new js,Cc=new X,vd=new X;class Jh extends mn{constructor(e=new Dt,t=new hh){super(),this.isLine=!0,this.type="Line",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}computeLineDistances(){const e=this.geometry;if(e.index===null){const t=e.attributes.position,r=[0];for(let i=1,s=t.count;i<s;i++)hl.fromBufferAttribute(t,i-1),fl.fromBufferAttribute(t,i),r[i]=r[i-1],r[i]+=hl.distanceTo(fl);e.setAttribute("lineDistance",new ui(r,1))}else $e("Line.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}raycast(e,t){const r=this.geometry,i=this.matrixWorld,s=e.params.Line.threshold,a=r.drawRange;if(r.boundingSphere===null&&r.computeBoundingSphere(),Ao.copy(r.boundingSphere),Ao.applyMatrix4(i),Ao.radius+=s,e.ray.intersectsSphere(Ao)===!1)return;_d.copy(i).invert(),_a.copy(e.ray).applyMatrix4(_d);const o=s/((this.scale.x+this.scale.y+this.scale.z)/3),l=o*o,c=this.isLineSegments?2:1,u=r.index,h=r.attributes.position;if(u!==null){const d=Math.max(0,a.start),m=Math.min(u.count,a.start+a.count);for(let g=d,p=m-1;g<p;g+=c){const _=u.getX(g),M=u.getX(g+1),y=Ro(this,e,_a,l,_,M,g);y&&t.push(y)}if(this.isLineLoop){const g=u.getX(m-1),p=u.getX(d),_=Ro(this,e,_a,l,g,p,m-1);_&&t.push(_)}}else{const d=Math.max(0,a.start),m=Math.min(h.count,a.start+a.count);for(let g=d,p=m-1;g<p;g+=c){const _=Ro(this,e,_a,l,g,g+1,g);_&&t.push(_)}if(this.isLineLoop){const g=Ro(this,e,_a,l,m-1,d,m-1);g&&t.push(g)}}}updateMorphTargets(){const t=this.geometry.morphAttributes,r=Object.keys(t);if(r.length>0){const i=t[r[0]];if(i!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let s=0,a=i.length;s<a;s++){const o=i[s].name||String(s);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=s}}}}}function Ro(n,e,t,r,i,s,a){const o=n.geometry.attributes.position;if(hl.fromBufferAttribute(o,i),fl.fromBufferAttribute(o,s),t.distanceSqToSegment(hl,fl,Cc,vd)>r)return;Cc.applyMatrix4(n.matrixWorld);const c=e.ray.origin.distanceTo(Cc);if(!(c<e.near||c>e.far))return{distance:c,point:vd.clone().applyMatrix4(n.matrixWorld),index:a,face:null,faceIndex:null,barycoord:null,object:n}}const xd=new X,Md=new X;class Pr extends Jh{constructor(e,t){super(e,t),this.isLineSegments=!0,this.type="LineSegments"}computeLineDistances(){const e=this.geometry;if(e.index===null){const t=e.attributes.position,r=[];for(let i=0,s=t.count;i<s;i+=2)xd.fromBufferAttribute(t,i),Md.fromBufferAttribute(t,i+1),r[i]=i===0?0:r[i-1],r[i+1]=r[i]+xd.distanceTo(Md);e.setAttribute("lineDistance",new ui(r,1))}else $e("LineSegments.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}}class Sd extends Jh{constructor(e,t){super(e,t),this.isLineLoop=!0,this.type="LineLoop"}}class Z_ extends Zi{constructor(e){super(),this.isPointsMaterial=!0,this.type="PointsMaterial",this.color=new lt(16777215),this.map=null,this.alphaMap=null,this.size=1,this.sizeAttenuation=!0,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.alphaMap=e.alphaMap,this.size=e.size,this.sizeAttenuation=e.sizeAttenuation,this.fog=e.fog,this}}const bd=new Ot,fh=new Rl,Co=new js,Po=new X;class $_ extends mn{constructor(e=new Dt,t=new Z_){super(),this.isPoints=!0,this.type="Points",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}raycast(e,t){const r=this.geometry,i=this.matrixWorld,s=e.params.Points.threshold,a=r.drawRange;if(r.boundingSphere===null&&r.computeBoundingSphere(),Co.copy(r.boundingSphere),Co.applyMatrix4(i),Co.radius+=s,e.ray.intersectsSphere(Co)===!1)return;bd.copy(i).invert(),fh.copy(e.ray).applyMatrix4(bd);const o=s/((this.scale.x+this.scale.y+this.scale.z)/3),l=o*o,c=r.index,f=r.attributes.position;if(c!==null){const h=Math.max(0,a.start),d=Math.min(c.count,a.start+a.count);for(let m=h,g=d;m<g;m++){const p=c.getX(m);Po.fromBufferAttribute(f,p),yd(Po,p,l,i,e,t,this)}}else{const h=Math.max(0,a.start),d=Math.min(f.count,a.start+a.count);for(let m=h,g=d;m<g;m++)Po.fromBufferAttribute(f,m),yd(Po,m,l,i,e,t,this)}}updateMorphTargets(){const t=this.geometry.morphAttributes,r=Object.keys(t);if(r.length>0){const i=t[r[0]];if(i!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let s=0,a=i.length;s<a;s++){const o=i[s].name||String(s);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=s}}}}}function yd(n,e,t,r,i,s,a){const o=fh.distanceSqToPoint(n);if(o<t){const l=new X;fh.closestPointToPoint(n,l),l.applyMatrix4(r);const c=i.ray.origin.distanceTo(l);if(c<i.near||c>i.far)return;s.push({distance:c,distanceToRay:Math.sqrt(o),point:l,index:e,face:null,faceIndex:null,barycoord:null,object:a})}}class Im extends Zt{constructor(e=[],t=jr,r,i,s,a,o,l,c,u){super(e,t,r,i,s,a,o,l,c,u),this.isCubeTexture=!0,this.flipY=!1}get images(){return this.image}set images(e){this.image=e}}class J_ extends Zt{constructor(e,t,r,i,s,a,o,l,c){super(e,t,r,i,s,a,o,l,c),this.isCanvasTexture=!0,this.needsUpdate=!0}}class Wi extends Zt{constructor(e,t,r=Di,i,s,a,o=cn,l=cn,c,u=qi,f=1){if(u!==qi&&u!==cr)throw new Error("DepthTexture format must be either THREE.DepthFormat or THREE.DepthStencilFormat");const h={width:e,height:t,depth:f};super(h,i,s,a,o,l,u,r,c),this.isDepthTexture=!0,this.flipY=!1,this.generateMipmaps=!1,this.compareFunction=null}copy(e){return super.copy(e),this.source=new Zh(Object.assign({},e.image)),this.compareFunction=e.compareFunction,this}toJSON(e){const t=super.toJSON(e);return this.compareFunction!==null&&(t.compareFunction=this.compareFunction),t}}class Q_ extends Wi{constructor(e,t=Di,r=jr,i,s,a=cn,o=cn,l,c=qi){const u={width:e,height:e,depth:1},f=[u,u,u,u,u,u];super(e,e,t,r,i,s,a,o,l,c),this.image=f,this.isCubeDepthTexture=!0,this.isCubeTexture=!0}get images(){return this.image}set images(e){this.image=e}}class Fm extends Zt{constructor(e=null){super(),this.sourceTexture=e,this.isExternalTexture=!0}copy(e){return super.copy(e),this.sourceTexture=e.sourceTexture,this}}class Ka extends Dt{constructor(e=1,t=1,r=1,i=1,s=1,a=1){super(),this.type="BoxGeometry",this.parameters={width:e,height:t,depth:r,widthSegments:i,heightSegments:s,depthSegments:a};const o=this;i=Math.floor(i),s=Math.floor(s),a=Math.floor(a);const l=[],c=[],u=[],f=[];let h=0,d=0;m("z","y","x",-1,-1,r,t,e,a,s,0),m("z","y","x",1,-1,r,t,-e,a,s,1),m("x","z","y",1,1,e,r,t,i,a,2),m("x","z","y",1,-1,e,r,-t,i,a,3),m("x","y","z",1,-1,e,t,r,i,s,4),m("x","y","z",-1,-1,e,t,-r,i,s,5),this.setIndex(l),this.setAttribute("position",new ui(c,3)),this.setAttribute("normal",new ui(u,3)),this.setAttribute("uv",new ui(f,2));function m(g,p,_,M,y,v,S,b,E,x,w){const R=v/E,L=S/x,A=v/2,U=S/2,P=b/2,I=E+1,F=x+1;let O=0,q=0;const z=new X;for(let k=0;k<F;k++){const N=k*L-U;for(let G=0;G<I;G++){const K=G*R-A;z[g]=K*M,z[p]=N*y,z[_]=P,c.push(z.x,z.y,z.z),z[g]=0,z[p]=0,z[_]=b>0?1:-1,u.push(z.x,z.y,z.z),f.push(G/E),f.push(1-k/x),O+=1}}for(let k=0;k<x;k++)for(let N=0;N<E;N++){const G=h+N+I*k,K=h+N+I*(k+1),J=h+(N+1)+I*(k+1),j=h+(N+1)+I*k;l.push(G,K,j),l.push(K,J,j),q+=6}o.addGroup(d,q,w),d+=q,h+=O}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new Ka(e.width,e.height,e.depth,e.widthSegments,e.heightSegments,e.depthSegments)}}class $r extends Dt{constructor(e=1,t=1,r=1,i=1){super(),this.type="PlaneGeometry",this.parameters={width:e,height:t,widthSegments:r,heightSegments:i};const s=e/2,a=t/2,o=Math.floor(r),l=Math.floor(i),c=o+1,u=l+1,f=e/o,h=t/l,d=[],m=[],g=[],p=[];for(let _=0;_<u;_++){const M=_*h-a;for(let y=0;y<c;y++){const v=y*f-s;m.push(v,-M,0),g.push(0,0,1),p.push(y/o),p.push(1-_/l)}}for(let _=0;_<l;_++)for(let M=0;M<o;M++){const y=M+c*_,v=M+c*(_+1),S=M+1+c*(_+1),b=M+1+c*_;d.push(y,v,b),d.push(v,S,b)}this.setIndex(d),this.setAttribute("position",new ui(m,3)),this.setAttribute("normal",new ui(g,3)),this.setAttribute("uv",new ui(p,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new $r(e.width,e.height,e.widthSegments,e.heightSegments)}}function zs(n){const e={};for(const t in n){e[t]={};for(const r in n[t]){const i=n[t][r];if(Td(i))i.isRenderTargetTexture?($e("UniformsUtils: Textures of render targets cannot be cloned via cloneUniforms() or mergeUniforms()."),e[t][r]=null):e[t][r]=i.clone();else if(Array.isArray(i))if(Td(i[0])){const s=[];for(let a=0,o=i.length;a<o;a++)s[a]=i[a].clone();e[t][r]=s}else e[t][r]=i.slice();else e[t][r]=i}}return e}function Mn(n){const e={};for(let t=0;t<n.length;t++){const r=zs(n[t]);for(const i in r)e[i]=r[i]}return e}function Td(n){return n&&(n.isColor||n.isMatrix3||n.isMatrix4||n.isVector2||n.isVector3||n.isVector4||n.isTexture||n.isQuaternion)}function ev(n){const e=[];for(let t=0;t<n.length;t++)e.push(n[t].clone());return e}function Nm(n){const e=n.getRenderTarget();return e===null?n.outputColorSpace:e.isXRRenderTarget===!0?e.texture.colorSpace:ut.workingColorSpace}const Om={clone:zs,merge:Mn};var tv=`void main() {
	gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
}`,nv=`void main() {
	gl_FragColor = vec4( 1.0, 0.0, 0.0, 1.0 );
}`;class an extends Zi{constructor(e){super(),this.isShaderMaterial=!0,this.type="ShaderMaterial",this.defines={},this.uniforms={},this.uniformsGroups=[],this.vertexShader=tv,this.fragmentShader=nv,this.linewidth=1,this.wireframe=!1,this.wireframeLinewidth=1,this.fog=!1,this.lights=!1,this.clipping=!1,this.forceSinglePass=!0,this.extensions={clipCullDistance:!1,multiDraw:!1},this.defaultAttributeValues={color:[1,1,1],uv:[0,0],uv1:[0,0]},this.index0AttributeName=void 0,this.uniformsNeedUpdate=!1,this.glslVersion=null,e!==void 0&&this.setValues(e)}copy(e){return super.copy(e),this.fragmentShader=e.fragmentShader,this.vertexShader=e.vertexShader,this.uniforms=zs(e.uniforms),this.uniformsGroups=ev(e.uniformsGroups),this.defines=Object.assign({},e.defines),this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.fog=e.fog,this.lights=e.lights,this.clipping=e.clipping,this.extensions=Object.assign({},e.extensions),this.glslVersion=e.glslVersion,this.defaultAttributeValues=Object.assign({},e.defaultAttributeValues),this.index0AttributeName=e.index0AttributeName,this.uniformsNeedUpdate=e.uniformsNeedUpdate,this}toJSON(e){const t=super.toJSON(e);t.glslVersion=this.glslVersion,t.uniforms={};for(const i in this.uniforms){const a=this.uniforms[i].value;a&&a.isTexture?t.uniforms[i]={type:"t",value:a.toJSON(e).uuid}:a&&a.isColor?t.uniforms[i]={type:"c",value:a.getHex()}:a&&a.isVector2?t.uniforms[i]={type:"v2",value:a.toArray()}:a&&a.isVector3?t.uniforms[i]={type:"v3",value:a.toArray()}:a&&a.isVector4?t.uniforms[i]={type:"v4",value:a.toArray()}:a&&a.isMatrix3?t.uniforms[i]={type:"m3",value:a.toArray()}:a&&a.isMatrix4?t.uniforms[i]={type:"m4",value:a.toArray()}:t.uniforms[i]={value:a}}Object.keys(this.defines).length>0&&(t.defines=this.defines),t.vertexShader=this.vertexShader,t.fragmentShader=this.fragmentShader,t.lights=this.lights,t.clipping=this.clipping;const r={};for(const i in this.extensions)this.extensions[i]===!0&&(r[i]=!0);return Object.keys(r).length>0&&(t.extensions=r),t}}class iv extends an{constructor(e){super(e),this.isRawShaderMaterial=!0,this.type="RawShaderMaterial"}}class Bm extends Zi{constructor(e){super(),this.isMeshDepthMaterial=!0,this.type="MeshDepthMaterial",this.depthPacking=ja,this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.wireframe=!1,this.wireframeLinewidth=1,this.setValues(e)}copy(e){return super.copy(e),this.depthPacking=e.depthPacking,this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this}}class km extends Zi{constructor(e){super(),this.isMeshDistanceMaterial=!0,this.type="MeshDistanceMaterial",this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.setValues(e)}copy(e){return super.copy(e),this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this}}const Do=new X,Uo=new vr,_i=new X;class zm extends mn{constructor(){super(),this.isCamera=!0,this.type="Camera",this.matrixWorldInverse=new Ot,this.projectionMatrix=new Ot,this.projectionMatrixInverse=new Ot,this.coordinateSystem=Ai,this._reversedDepth=!1}get reversedDepth(){return this._reversedDepth}copy(e,t){return super.copy(e,t),this.matrixWorldInverse.copy(e.matrixWorldInverse),this.projectionMatrix.copy(e.projectionMatrix),this.projectionMatrixInverse.copy(e.projectionMatrixInverse),this.coordinateSystem=e.coordinateSystem,this}getWorldDirection(e){return super.getWorldDirection(e).negate()}updateMatrixWorld(e){super.updateMatrixWorld(e),this.matrixWorld.decompose(Do,Uo,_i),_i.x===1&&_i.y===1&&_i.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(Do,Uo,_i.set(1,1,1)).invert()}updateWorldMatrix(e,t){super.updateWorldMatrix(e,t),this.matrixWorld.decompose(Do,Uo,_i),_i.x===1&&_i.y===1&&_i.z===1?this.matrixWorldInverse.copy(this.matrixWorld).invert():this.matrixWorldInverse.compose(Do,Uo,_i.set(1,1,1)).invert()}clone(){return new this.constructor().copy(this)}}const ar=new X,Ed=new We,wd=new We;class kn extends zm{constructor(e=50,t=1,r=.1,i=2e3){super(),this.isPerspectiveCamera=!0,this.type="PerspectiveCamera",this.fov=e,this.zoom=1,this.near=r,this.far=i,this.focus=10,this.aspect=t,this.view=null,this.filmGauge=35,this.filmOffset=0,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.fov=e.fov,this.zoom=e.zoom,this.near=e.near,this.far=e.far,this.focus=e.focus,this.aspect=e.aspect,this.view=e.view===null?null:Object.assign({},e.view),this.filmGauge=e.filmGauge,this.filmOffset=e.filmOffset,this}setFocalLength(e){const t=.5*this.getFilmHeight()/e;this.fov=ch*2*Math.atan(t),this.updateProjectionMatrix()}getFocalLength(){const e=Math.tan(jo*.5*this.fov);return .5*this.getFilmHeight()/e}getEffectiveFOV(){return ch*2*Math.atan(Math.tan(jo*.5*this.fov)/this.zoom)}getFilmWidth(){return this.filmGauge*Math.min(this.aspect,1)}getFilmHeight(){return this.filmGauge/Math.max(this.aspect,1)}getViewBounds(e,t,r){ar.set(-1,-1,.5).applyMatrix4(this.projectionMatrixInverse),t.set(ar.x,ar.y).multiplyScalar(-e/ar.z),ar.set(1,1,.5).applyMatrix4(this.projectionMatrixInverse),r.set(ar.x,ar.y).multiplyScalar(-e/ar.z)}getViewSize(e,t){return this.getViewBounds(e,Ed,wd),t.subVectors(wd,Ed)}setViewOffset(e,t,r,i,s,a){this.aspect=e/t,this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=r,this.view.offsetY=i,this.view.width=s,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){const e=this.near;let t=e*Math.tan(jo*.5*this.fov)/this.zoom,r=2*t,i=this.aspect*r,s=-.5*i;const a=this.view;if(this.view!==null&&this.view.enabled){const l=a.fullWidth,c=a.fullHeight;s+=a.offsetX*i/l,t-=a.offsetY*r/c,i*=a.width/l,r*=a.height/c}const o=this.filmOffset;o!==0&&(s+=e*o/this.getFilmWidth()),this.projectionMatrix.makePerspective(s,s+i,t,t-r,e,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){const t=super.toJSON(e);return t.object.fov=this.fov,t.object.zoom=this.zoom,t.object.near=this.near,t.object.far=this.far,t.object.focus=this.focus,t.object.aspect=this.aspect,this.view!==null&&(t.object.view=Object.assign({},this.view)),t.object.filmGauge=this.filmGauge,t.object.filmOffset=this.filmOffset,t}}class Qh extends zm{constructor(e=-1,t=1,r=1,i=-1,s=.1,a=2e3){super(),this.isOrthographicCamera=!0,this.type="OrthographicCamera",this.zoom=1,this.view=null,this.left=e,this.right=t,this.top=r,this.bottom=i,this.near=s,this.far=a,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.left=e.left,this.right=e.right,this.top=e.top,this.bottom=e.bottom,this.near=e.near,this.far=e.far,this.zoom=e.zoom,this.view=e.view===null?null:Object.assign({},e.view),this}setViewOffset(e,t,r,i,s,a){this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=r,this.view.offsetY=i,this.view.width=s,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){const e=(this.right-this.left)/(2*this.zoom),t=(this.top-this.bottom)/(2*this.zoom),r=(this.right+this.left)/2,i=(this.top+this.bottom)/2;let s=r-e,a=r+e,o=i+t,l=i-t;if(this.view!==null&&this.view.enabled){const c=(this.right-this.left)/this.view.fullWidth/this.zoom,u=(this.top-this.bottom)/this.view.fullHeight/this.zoom;s+=c*this.view.offsetX,a=s+c*this.view.width,o-=u*this.view.offsetY,l=o-u*this.view.height}this.projectionMatrix.makeOrthographic(s,a,o,l,this.near,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){const t=super.toJSON(e);return t.object.zoom=this.zoom,t.object.left=this.left,t.object.right=this.right,t.object.top=this.top,t.object.bottom=this.bottom,t.object.near=this.near,t.object.far=this.far,this.view!==null&&(t.object.view=Object.assign({},this.view)),t}}class rv extends Dt{constructor(){super(),this.isInstancedBufferGeometry=!0,this.type="InstancedBufferGeometry",this.instanceCount=1/0}copy(e){return super.copy(e),this.instanceCount=e.instanceCount,this}toJSON(){const e=super.toJSON();return e.instanceCount=this.instanceCount,e.isInstancedBufferGeometry=!0,e}}const Ss=-90,bs=1;class sv extends mn{constructor(e,t,r){super(),this.type="CubeCamera",this.renderTarget=r,this.coordinateSystem=null,this.activeMipmapLevel=0;const i=new kn(Ss,bs,e,t);i.layers=this.layers,this.add(i);const s=new kn(Ss,bs,e,t);s.layers=this.layers,this.add(s);const a=new kn(Ss,bs,e,t);a.layers=this.layers,this.add(a);const o=new kn(Ss,bs,e,t);o.layers=this.layers,this.add(o);const l=new kn(Ss,bs,e,t);l.layers=this.layers,this.add(l);const c=new kn(Ss,bs,e,t);c.layers=this.layers,this.add(c)}updateCoordinateSystem(){const e=this.coordinateSystem,t=this.children.concat(),[r,i,s,a,o,l]=t;for(const c of t)this.remove(c);if(e===Ai)r.up.set(0,1,0),r.lookAt(1,0,0),i.up.set(0,1,0),i.lookAt(-1,0,0),s.up.set(0,0,-1),s.lookAt(0,1,0),a.up.set(0,0,1),a.lookAt(0,-1,0),o.up.set(0,1,0),o.lookAt(0,0,1),l.up.set(0,1,0),l.lookAt(0,0,-1);else if(e===ol)r.up.set(0,-1,0),r.lookAt(-1,0,0),i.up.set(0,-1,0),i.lookAt(1,0,0),s.up.set(0,0,1),s.lookAt(0,1,0),a.up.set(0,0,-1),a.lookAt(0,-1,0),o.up.set(0,-1,0),o.lookAt(0,0,1),l.up.set(0,-1,0),l.lookAt(0,0,-1);else throw new Error("THREE.CubeCamera.updateCoordinateSystem(): Invalid coordinate system: "+e);for(const c of t)this.add(c),c.updateMatrixWorld()}update(e,t){this.parent===null&&this.updateMatrixWorld();const{renderTarget:r,activeMipmapLevel:i}=this;this.coordinateSystem!==e.coordinateSystem&&(this.coordinateSystem=e.coordinateSystem,this.updateCoordinateSystem());const[s,a,o,l,c,u]=this.children,f=e.getRenderTarget(),h=e.getActiveCubeFace(),d=e.getActiveMipmapLevel(),m=e.xr.enabled;e.xr.enabled=!1;const g=r.texture.generateMipmaps;r.texture.generateMipmaps=!1;let p=!1;e.isWebGLRenderer===!0?p=e.state.buffers.depth.getReversed():p=e.reversedDepthBuffer,e.setRenderTarget(r,0,i),p&&e.autoClear===!1&&e.clearDepth(),e.render(t,s),e.setRenderTarget(r,1,i),p&&e.autoClear===!1&&e.clearDepth(),e.render(t,a),e.setRenderTarget(r,2,i),p&&e.autoClear===!1&&e.clearDepth(),e.render(t,o),e.setRenderTarget(r,3,i),p&&e.autoClear===!1&&e.clearDepth(),e.render(t,l),e.setRenderTarget(r,4,i),p&&e.autoClear===!1&&e.clearDepth(),e.render(t,c),r.texture.generateMipmaps=g,e.setRenderTarget(r,5,i),p&&e.autoClear===!1&&e.clearDepth(),e.render(t,u),e.setRenderTarget(f,h,d),e.xr.enabled=m,r.texture.needsPMREMUpdate=!0}}class av extends kn{constructor(e=[]){super(),this.isArrayCamera=!0,this.isMultiViewCamera=!1,this.cameras=e}}class gt{constructor(e){this.value=e}clone(){return new gt(this.value.clone===void 0?this.value:this.value.clone())}}class ov{constructor(e=!0){this.autoStart=e,this.startTime=0,this.oldTime=0,this.elapsedTime=0,this.running=!1,$e("Clock: This module has been deprecated. Please use THREE.Timer instead.")}start(){this.startTime=performance.now(),this.oldTime=this.startTime,this.elapsedTime=0,this.running=!0}stop(){this.getElapsedTime(),this.running=!1,this.autoStart=!1}getElapsedTime(){return this.getDelta(),this.elapsedTime}getDelta(){let e=0;if(this.autoStart&&!this.running)return this.start(),0;if(this.running){const t=performance.now();e=(t-this.oldTime)/1e3,this.oldTime=t,this.elapsedTime+=e}return e}}class Ad{constructor(e=1,t=0,r=0){this.radius=e,this.phi=t,this.theta=r}set(e,t,r){return this.radius=e,this.phi=t,this.theta=r,this}copy(e){return this.radius=e.radius,this.phi=e.phi,this.theta=e.theta,this}makeSafe(){return this.phi=at(this.phi,1e-6,Math.PI-1e-6),this}setFromVector3(e){return this.setFromCartesianCoords(e.x,e.y,e.z)}setFromCartesianCoords(e,t,r){return this.radius=Math.sqrt(e*e+t*t+r*r),this.radius===0?(this.theta=0,this.phi=0):(this.theta=Math.atan2(e,r),this.phi=Math.acos(at(t/this.radius,-1,1))),this}clone(){return new this.constructor().copy(this)}}const Nf=class Nf{constructor(e,t,r,i){this.elements=[1,0,0,1],e!==void 0&&this.set(e,t,r,i)}identity(){return this.set(1,0,0,1),this}fromArray(e,t=0){for(let r=0;r<4;r++)this.elements[r]=e[r+t];return this}set(e,t,r,i){const s=this.elements;return s[0]=e,s[2]=t,s[1]=r,s[3]=i,this}};Nf.prototype.isMatrix2=!0;let Rd=Nf;class lv extends hi{constructor(e,t=null){super(),this.object=e,this.domElement=t,this.enabled=!0,this.state=-1,this.keys={},this.mouseButtons={LEFT:null,MIDDLE:null,RIGHT:null},this.touches={ONE:null,TWO:null}}connect(e){if(e===void 0){$e("Controls: connect() now requires an element.");return}this.domElement!==null&&this.disconnect(),this.domElement=e}disconnect(){}dispose(){}update(){}}function Cd(n,e,t,r){const i=cv(r);switch(t){case ym:return n*e;case Em:return n*e/i.components*i.byteLength;case Xh:return n*e/i.components*i.byteLength;case Kr:return n*e*2/i.components*i.byteLength;case Yh:return n*e*2/i.components*i.byteLength;case Tm:return n*e*3/i.components*i.byteLength;case ci:return n*e*4/i.components*i.byteLength;case qh:return n*e*4/i.components*i.byteLength;case Wo:case Xo:return Math.floor((n+3)/4)*Math.floor((e+3)/4)*8;case Yo:case qo:return Math.floor((n+3)/4)*Math.floor((e+3)/4)*16;case Uu:case Iu:return Math.max(n,16)*Math.max(e,8)/4;case Du:case Lu:return Math.max(n,8)*Math.max(e,8)/2;case Fu:case Nu:case Bu:case ku:return Math.floor((n+3)/4)*Math.floor((e+3)/4)*8;case Ou:case rl:case zu:return Math.floor((n+3)/4)*Math.floor((e+3)/4)*16;case Gu:return Math.floor((n+3)/4)*Math.floor((e+3)/4)*16;case Hu:return Math.floor((n+4)/5)*Math.floor((e+3)/4)*16;case Vu:return Math.floor((n+4)/5)*Math.floor((e+4)/5)*16;case Wu:return Math.floor((n+5)/6)*Math.floor((e+4)/5)*16;case Xu:return Math.floor((n+5)/6)*Math.floor((e+5)/6)*16;case Yu:return Math.floor((n+7)/8)*Math.floor((e+4)/5)*16;case qu:return Math.floor((n+7)/8)*Math.floor((e+5)/6)*16;case ju:return Math.floor((n+7)/8)*Math.floor((e+7)/8)*16;case Ku:return Math.floor((n+9)/10)*Math.floor((e+4)/5)*16;case Zu:return Math.floor((n+9)/10)*Math.floor((e+5)/6)*16;case $u:return Math.floor((n+9)/10)*Math.floor((e+7)/8)*16;case Ju:return Math.floor((n+9)/10)*Math.floor((e+9)/10)*16;case Qu:return Math.floor((n+11)/12)*Math.floor((e+9)/10)*16;case eh:return Math.floor((n+11)/12)*Math.floor((e+11)/12)*16;case th:case nh:case ih:return Math.ceil(n/4)*Math.ceil(e/4)*16;case rh:case sh:return Math.ceil(n/4)*Math.ceil(e/4)*8;case sl:case ah:return Math.ceil(n/4)*Math.ceil(e/4)*16}throw new Error(`Unable to determine texture byte length for ${t} format.`)}function cv(n){switch(n){case Yt:case xm:return{byteLength:1,components:1};case Oa:case Mm:case Yi:return{byteLength:2,components:1};case Vh:case Wh:return{byteLength:2,components:4};case Di:case Hh:case li:return{byteLength:4,components:1};case Sm:case bm:return{byteLength:4,components:3}}throw new Error(`Unknown texture type ${n}.`)}typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("register",{detail:{revision:qa}}));typeof window<"u"&&(window.__THREE__?$e("WARNING: Multiple instances of Three.js being imported."):window.__THREE__=qa);/**
 * @license
 * Copyright 2010-2026 Three.js Authors
 * SPDX-License-Identifier: MIT
 */function Gm(){let n=null,e=!1,t=null,r=null;function i(s,a){t(s,a),r=n.requestAnimationFrame(i)}return{start:function(){e!==!0&&t!==null&&n!==null&&(r=n.requestAnimationFrame(i),e=!0)},stop:function(){n!==null&&n.cancelAnimationFrame(r),e=!1},setAnimationLoop:function(s){t=s},setContext:function(s){n=s}}}function uv(n){const e=new WeakMap;function t(o,l){const c=o.array,u=o.usage,f=c.byteLength,h=n.createBuffer();n.bindBuffer(l,h),n.bufferData(l,c,u),o.onUploadCallback();let d;if(c instanceof Float32Array)d=n.FLOAT;else if(typeof Float16Array<"u"&&c instanceof Float16Array)d=n.HALF_FLOAT;else if(c instanceof Uint16Array)o.isFloat16BufferAttribute?d=n.HALF_FLOAT:d=n.UNSIGNED_SHORT;else if(c instanceof Int16Array)d=n.SHORT;else if(c instanceof Uint32Array)d=n.UNSIGNED_INT;else if(c instanceof Int32Array)d=n.INT;else if(c instanceof Int8Array)d=n.BYTE;else if(c instanceof Uint8Array)d=n.UNSIGNED_BYTE;else if(c instanceof Uint8ClampedArray)d=n.UNSIGNED_BYTE;else throw new Error("THREE.WebGLAttributes: Unsupported buffer data format: "+c);return{buffer:h,type:d,bytesPerElement:c.BYTES_PER_ELEMENT,version:o.version,size:f}}function r(o,l,c){const u=l.array,f=l.updateRanges;if(n.bindBuffer(c,o),f.length===0)n.bufferSubData(c,0,u);else{f.sort((d,m)=>d.start-m.start);let h=0;for(let d=1;d<f.length;d++){const m=f[h],g=f[d];g.start<=m.start+m.count+1?m.count=Math.max(m.count,g.start+g.count-m.start):(++h,f[h]=g)}f.length=h+1;for(let d=0,m=f.length;d<m;d++){const g=f[d];n.bufferSubData(c,g.start*u.BYTES_PER_ELEMENT,u,g.start,g.count)}l.clearUpdateRanges()}l.onUploadCallback()}function i(o){return o.isInterleavedBufferAttribute&&(o=o.data),e.get(o)}function s(o){o.isInterleavedBufferAttribute&&(o=o.data);const l=e.get(o);l&&(n.deleteBuffer(l.buffer),e.delete(o))}function a(o,l){if(o.isInterleavedBufferAttribute&&(o=o.data),o.isGLBufferAttribute){const u=e.get(o);(!u||u.version<o.version)&&e.set(o,{buffer:o.buffer,type:o.type,bytesPerElement:o.elementSize,version:o.version});return}const c=e.get(o);if(c===void 0)e.set(o,t(o,l));else if(c.version<o.version){if(c.size!==o.array.byteLength)throw new Error("THREE.WebGLAttributes: The size of the buffer attribute's array buffer does not match the original size. Resizing buffer attributes is not supported.");r(c.buffer,o,l),c.version=o.version}}return{get:i,remove:s,update:a}}var hv=`#ifdef USE_ALPHAHASH
	if ( diffuseColor.a < getAlphaHashThreshold( vPosition ) ) discard;
#endif`,fv=`#ifdef USE_ALPHAHASH
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
#endif`,dv=`#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, vAlphaMapUv ).g;
#endif`,pv=`#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,mv=`#ifdef USE_ALPHATEST
	#ifdef ALPHA_TO_COVERAGE
	diffuseColor.a = smoothstep( alphaTest, alphaTest + fwidth( diffuseColor.a ), diffuseColor.a );
	if ( diffuseColor.a == 0.0 ) discard;
	#else
	if ( diffuseColor.a < alphaTest ) discard;
	#endif
#endif`,gv=`#ifdef USE_ALPHATEST
	uniform float alphaTest;
#endif`,_v=`#ifdef USE_AOMAP
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
#endif`,vv=`#ifdef USE_AOMAP
	uniform sampler2D aoMap;
	uniform float aoMapIntensity;
#endif`,xv=`#ifdef USE_BATCHING
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
#endif`,Mv=`#ifdef USE_BATCHING
	mat4 batchingMatrix = getBatchingMatrix( getIndirectIndex( gl_DrawID ) );
#endif`,Sv=`vec3 transformed = vec3( position );
#ifdef USE_ALPHAHASH
	vPosition = vec3( position );
#endif`,bv=`vec3 objectNormal = vec3( normal );
#ifdef USE_TANGENT
	vec3 objectTangent = vec3( tangent.xyz );
#endif`,yv=`float G_BlinnPhong_Implicit( ) {
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
} // validated`,Tv=`#ifdef USE_IRIDESCENCE
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
#endif`,Ev=`#ifdef USE_BUMPMAP
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
#endif`,wv=`#if NUM_CLIPPING_PLANES > 0
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
#endif`,Av=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
	uniform vec4 clippingPlanes[ NUM_CLIPPING_PLANES ];
#endif`,Rv=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
#endif`,Cv=`#if NUM_CLIPPING_PLANES > 0
	vClipPosition = - mvPosition.xyz;
#endif`,Pv=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	diffuseColor *= vColor;
#endif`,Dv=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#endif`,Uv=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	varying vec4 vColor;
#endif`,Lv=`#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
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
#endif`,Iv=`#define PI 3.141592653589793
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
} // validated`,Fv=`#ifdef ENVMAP_TYPE_CUBE_UV
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
#endif`,Nv=`vec3 transformedNormal = objectNormal;
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
#endif`,Ov=`#ifdef USE_DISPLACEMENTMAP
	uniform sampler2D displacementMap;
	uniform float displacementScale;
	uniform float displacementBias;
#endif`,Bv=`#ifdef USE_DISPLACEMENTMAP
	transformed += normalize( objectNormal ) * ( texture2D( displacementMap, vDisplacementMapUv ).x * displacementScale + displacementBias );
#endif`,kv=`#ifdef USE_EMISSIVEMAP
	vec4 emissiveColor = texture2D( emissiveMap, vEmissiveMapUv );
	#ifdef DECODE_VIDEO_TEXTURE_EMISSIVE
		emissiveColor = sRGBTransferEOTF( emissiveColor );
	#endif
	totalEmissiveRadiance *= emissiveColor.rgb;
#endif`,zv=`#ifdef USE_EMISSIVEMAP
	uniform sampler2D emissiveMap;
#endif`,Gv="gl_FragColor = linearToOutputTexel( gl_FragColor );",Hv=`vec4 LinearTransferOETF( in vec4 value ) {
	return value;
}
vec4 sRGBTransferEOTF( in vec4 value ) {
	return vec4( mix( pow( value.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), value.rgb * 0.0773993808, vec3( lessThanEqual( value.rgb, vec3( 0.04045 ) ) ) ), value.a );
}
vec4 sRGBTransferOETF( in vec4 value ) {
	return vec4( mix( pow( value.rgb, vec3( 0.41666 ) ) * 1.055 - vec3( 0.055 ), value.rgb * 12.92, vec3( lessThanEqual( value.rgb, vec3( 0.0031308 ) ) ) ), value.a );
}`,Vv=`#ifdef USE_ENVMAP
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
#endif`,Wv=`#ifdef USE_ENVMAP
	uniform float envMapIntensity;
	uniform mat3 envMapRotation;
	#ifdef ENVMAP_TYPE_CUBE
		uniform samplerCube envMap;
	#else
		uniform sampler2D envMap;
	#endif
#endif`,Xv=`#ifdef USE_ENVMAP
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
#endif`,Yv=`#ifdef USE_ENVMAP
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		
		varying vec3 vWorldPosition;
	#else
		varying vec3 vReflect;
		uniform float refractionRatio;
	#endif
#endif`,qv=`#ifdef USE_ENVMAP
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
#endif`,jv=`#ifdef USE_FOG
	vFogDepth = - mvPosition.z;
#endif`,Kv=`#ifdef USE_FOG
	varying float vFogDepth;
#endif`,Zv=`#ifdef USE_FOG
	#ifdef FOG_EXP2
		float fogFactor = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
	#else
		float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
	#endif
	gl_FragColor.rgb = mix( gl_FragColor.rgb, fogColor, fogFactor );
#endif`,$v=`#ifdef USE_FOG
	uniform vec3 fogColor;
	varying float vFogDepth;
	#ifdef FOG_EXP2
		uniform float fogDensity;
	#else
		uniform float fogNear;
		uniform float fogFar;
	#endif
#endif`,Jv=`#ifdef USE_GRADIENTMAP
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
}`,Qv=`#ifdef USE_LIGHTMAP
	uniform sampler2D lightMap;
	uniform float lightMapIntensity;
#endif`,ex=`LambertMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularStrength = specularStrength;`,tx=`varying vec3 vViewPosition;
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
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Lambert`,nx=`uniform bool receiveShadow;
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
#include <lightprobes_pars_fragment>`,ix=`#ifdef USE_ENVMAP
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
#endif`,rx=`ToonMaterial material;
material.diffuseColor = diffuseColor.rgb;`,sx=`varying vec3 vViewPosition;
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
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Toon`,ax=`BlinnPhongMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularColor = specular;
material.specularShininess = shininess;
material.specularStrength = specularStrength;`,ox=`varying vec3 vViewPosition;
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
#define RE_IndirectDiffuse		RE_IndirectDiffuse_BlinnPhong`,lx=`PhysicalMaterial material;
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
#endif`,cx=`uniform sampler2D dfgLUT;
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
}`,ux=`
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
#endif`,hx=`#if defined( RE_IndirectDiffuse )
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
#endif`,fx=`#if defined( RE_IndirectDiffuse )
	#if defined( LAMBERT ) || defined( PHONG )
		irradiance += iblIrradiance;
	#endif
	RE_IndirectDiffuse( irradiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif
#if defined( RE_IndirectSpecular )
	RE_IndirectSpecular( radiance, iblIrradiance, clearcoatRadiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif`,dx=`#ifdef USE_LIGHT_PROBES_GRID
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
#endif`,px=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	gl_FragDepth = vIsPerspective == 0.0 ? gl_FragCoord.z : log2( vFragDepth ) * logDepthBufFC * 0.5;
#endif`,mx=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	uniform float logDepthBufFC;
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,gx=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,_x=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	vFragDepth = 1.0 + gl_Position.w;
	vIsPerspective = float( isPerspectiveMatrix( projectionMatrix ) );
#endif`,vx=`#ifdef USE_MAP
	vec4 sampledDiffuseColor = texture2D( map, vMapUv );
	#ifdef DECODE_VIDEO_TEXTURE
		sampledDiffuseColor = sRGBTransferEOTF( sampledDiffuseColor );
	#endif
	diffuseColor *= sampledDiffuseColor;
#endif`,xx=`#ifdef USE_MAP
	uniform sampler2D map;
#endif`,Mx=`#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
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
#endif`,Sx=`#if defined( USE_POINTS_UV )
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
#endif`,bx=`float metalnessFactor = metalness;
#ifdef USE_METALNESSMAP
	vec4 texelMetalness = texture2D( metalnessMap, vMetalnessMapUv );
	metalnessFactor *= texelMetalness.b;
#endif`,yx=`#ifdef USE_METALNESSMAP
	uniform sampler2D metalnessMap;
#endif`,Tx=`#ifdef USE_INSTANCING_MORPH
	float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	float morphTargetBaseInfluence = texelFetch( morphTexture, ivec2( 0, gl_InstanceID ), 0 ).r;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		morphTargetInfluences[i] =  texelFetch( morphTexture, ivec2( i + 1, gl_InstanceID ), 0 ).r;
	}
#endif`,Ex=`#if defined( USE_MORPHCOLORS )
	vColor *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		#if defined( USE_COLOR_ALPHA )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ) * morphTargetInfluences[ i ];
		#elif defined( USE_COLOR )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ).rgb * morphTargetInfluences[ i ];
		#endif
	}
#endif`,wx=`#ifdef USE_MORPHNORMALS
	objectNormal *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) objectNormal += getMorph( gl_VertexID, i, 1 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,Ax=`#ifdef USE_MORPHTARGETS
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
#endif`,Rx=`#ifdef USE_MORPHTARGETS
	transformed *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) transformed += getMorph( gl_VertexID, i, 0 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,Cx=`float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;
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
vec3 nonPerturbedNormal = normal;`,Px=`#ifdef USE_NORMALMAP_OBJECTSPACE
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
#endif`,Dx=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,Ux=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,Lx=`#ifndef FLAT_SHADED
	vNormal = normalize( transformedNormal );
	#ifdef USE_TANGENT
		vTangent = normalize( transformedTangent );
		vBitangent = normalize( cross( vNormal, vTangent ) * tangent.w );
	#endif
#endif`,Ix=`#ifdef USE_NORMALMAP
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
#endif`,Fx=`#ifdef USE_CLEARCOAT
	vec3 clearcoatNormal = nonPerturbedNormal;
#endif`,Nx=`#ifdef USE_CLEARCOAT_NORMALMAP
	vec3 clearcoatMapN = texture2D( clearcoatNormalMap, vClearcoatNormalMapUv ).xyz * 2.0 - 1.0;
	clearcoatMapN.xy *= clearcoatNormalScale;
	clearcoatNormal = normalize( tbn2 * clearcoatMapN );
#endif`,Ox=`#ifdef USE_CLEARCOATMAP
	uniform sampler2D clearcoatMap;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform sampler2D clearcoatNormalMap;
	uniform vec2 clearcoatNormalScale;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform sampler2D clearcoatRoughnessMap;
#endif`,Bx=`#ifdef USE_IRIDESCENCEMAP
	uniform sampler2D iridescenceMap;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform sampler2D iridescenceThicknessMap;
#endif`,kx=`#ifdef OPAQUE
diffuseColor.a = 1.0;
#endif
#ifdef USE_TRANSMISSION
diffuseColor.a *= material.transmissionAlpha;
#endif
gl_FragColor = vec4( outgoingLight, diffuseColor.a );`,zx=`vec3 packNormalToRGB( const in vec3 normal ) {
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
}`,Gx=`#ifdef PREMULTIPLIED_ALPHA
	gl_FragColor.rgb *= gl_FragColor.a;
#endif`,Hx=`vec4 mvPosition = vec4( transformed, 1.0 );
#ifdef USE_BATCHING
	mvPosition = batchingMatrix * mvPosition;
#endif
#ifdef USE_INSTANCING
	mvPosition = instanceMatrix * mvPosition;
#endif
mvPosition = modelViewMatrix * mvPosition;
gl_Position = projectionMatrix * mvPosition;`,Vx=`#ifdef DITHERING
	gl_FragColor.rgb = dithering( gl_FragColor.rgb );
#endif`,Wx=`#ifdef DITHERING
	vec3 dithering( vec3 color ) {
		float grid_position = rand( gl_FragCoord.xy );
		vec3 dither_shift_RGB = vec3( 0.25 / 255.0, -0.25 / 255.0, 0.25 / 255.0 );
		dither_shift_RGB = mix( 2.0 * dither_shift_RGB, -2.0 * dither_shift_RGB, grid_position );
		return color + dither_shift_RGB;
	}
#endif`,Xx=`float roughnessFactor = roughness;
#ifdef USE_ROUGHNESSMAP
	vec4 texelRoughness = texture2D( roughnessMap, vRoughnessMapUv );
	roughnessFactor *= texelRoughness.g;
#endif`,Yx=`#ifdef USE_ROUGHNESSMAP
	uniform sampler2D roughnessMap;
#endif`,qx=`#if NUM_SPOT_LIGHT_COORDS > 0
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
#endif`,jx=`#if NUM_SPOT_LIGHT_COORDS > 0
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
#endif`,Kx=`#if ( defined( USE_SHADOWMAP ) && ( NUM_DIR_LIGHT_SHADOWS > 0 || NUM_POINT_LIGHT_SHADOWS > 0 ) ) || ( NUM_SPOT_LIGHT_COORDS > 0 )
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
#endif`,Zx=`float getShadowMask() {
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
}`,$x=`#ifdef USE_SKINNING
	mat4 boneMatX = getBoneMatrix( skinIndex.x );
	mat4 boneMatY = getBoneMatrix( skinIndex.y );
	mat4 boneMatZ = getBoneMatrix( skinIndex.z );
	mat4 boneMatW = getBoneMatrix( skinIndex.w );
#endif`,Jx=`#ifdef USE_SKINNING
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
#endif`,Qx=`#ifdef USE_SKINNING
	vec4 skinVertex = bindMatrix * vec4( transformed, 1.0 );
	vec4 skinned = vec4( 0.0 );
	skinned += boneMatX * skinVertex * skinWeight.x;
	skinned += boneMatY * skinVertex * skinWeight.y;
	skinned += boneMatZ * skinVertex * skinWeight.z;
	skinned += boneMatW * skinVertex * skinWeight.w;
	transformed = ( bindMatrixInverse * skinned ).xyz;
#endif`,e1=`#ifdef USE_SKINNING
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
#endif`,t1=`float specularStrength;
#ifdef USE_SPECULARMAP
	vec4 texelSpecular = texture2D( specularMap, vSpecularMapUv );
	specularStrength = texelSpecular.r;
#else
	specularStrength = 1.0;
#endif`,n1=`#ifdef USE_SPECULARMAP
	uniform sampler2D specularMap;
#endif`,i1=`#if defined( TONE_MAPPING )
	gl_FragColor.rgb = toneMapping( gl_FragColor.rgb );
#endif`,r1=`#ifndef saturate
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
vec3 CustomToneMapping( vec3 color ) { return color; }`,s1=`#ifdef USE_TRANSMISSION
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
#endif`,a1=`#ifdef USE_TRANSMISSION
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
#endif`,o1=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
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
#endif`,l1=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
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
#endif`,c1=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
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
#endif`,u1=`#if defined( USE_ENVMAP ) || defined( DISTANCE ) || defined ( USE_SHADOWMAP ) || defined ( USE_TRANSMISSION ) || NUM_SPOT_LIGHT_COORDS > 0
	vec4 worldPosition = vec4( transformed, 1.0 );
	#ifdef USE_BATCHING
		worldPosition = batchingMatrix * worldPosition;
	#endif
	#ifdef USE_INSTANCING
		worldPosition = instanceMatrix * worldPosition;
	#endif
	worldPosition = modelMatrix * worldPosition;
#endif`;const h1=`varying vec2 vUv;
uniform mat3 uvTransform;
void main() {
	vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	gl_Position = vec4( position.xy, 1.0, 1.0 );
}`,f1=`uniform sampler2D t2D;
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
}`,d1=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,p1=`#ifdef ENVMAP_TYPE_CUBE
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
}`,m1=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,g1=`uniform samplerCube tCube;
uniform float tFlip;
uniform float opacity;
varying vec3 vWorldDirection;
void main() {
	vec4 texColor = textureCube( tCube, vec3( tFlip * vWorldDirection.x, vWorldDirection.yz ) );
	gl_FragColor = texColor;
	gl_FragColor.a *= opacity;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,_1=`#include <common>
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
}`,v1=`#if DEPTH_PACKING == 3200
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
}`,x1=`#define DISTANCE
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
}`,M1=`#define DISTANCE
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
}`,S1=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
}`,b1=`uniform sampler2D tEquirect;
varying vec3 vWorldDirection;
#include <common>
void main() {
	vec3 direction = normalize( vWorldDirection );
	vec2 sampleUV = equirectUv( direction );
	gl_FragColor = texture2D( tEquirect, sampleUV );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,y1=`uniform float scale;
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
}`,T1=`uniform vec3 diffuse;
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
}`,E1=`#include <common>
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
}`,w1=`uniform vec3 diffuse;
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
}`,A1=`#define LAMBERT
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
}`,R1=`#define LAMBERT
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
}`,C1=`#define MATCAP
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
}`,P1=`#define MATCAP
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
}`,D1=`#define NORMAL
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
}`,U1=`#define NORMAL
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
}`,L1=`#define PHONG
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
}`,I1=`#define PHONG
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
}`,F1=`#define STANDARD
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
}`,N1=`#define STANDARD
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
}`,O1=`#define TOON
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
}`,B1=`#define TOON
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
}`,k1=`uniform float size;
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
}`,z1=`uniform vec3 diffuse;
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
}`,G1=`#include <common>
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
}`,H1=`uniform vec3 color;
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
}`,V1=`uniform float rotation;
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
}`,W1=`uniform vec3 diffuse;
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
}`,it={alphahash_fragment:hv,alphahash_pars_fragment:fv,alphamap_fragment:dv,alphamap_pars_fragment:pv,alphatest_fragment:mv,alphatest_pars_fragment:gv,aomap_fragment:_v,aomap_pars_fragment:vv,batching_pars_vertex:xv,batching_vertex:Mv,begin_vertex:Sv,beginnormal_vertex:bv,bsdfs:yv,iridescence_fragment:Tv,bumpmap_pars_fragment:Ev,clipping_planes_fragment:wv,clipping_planes_pars_fragment:Av,clipping_planes_pars_vertex:Rv,clipping_planes_vertex:Cv,color_fragment:Pv,color_pars_fragment:Dv,color_pars_vertex:Uv,color_vertex:Lv,common:Iv,cube_uv_reflection_fragment:Fv,defaultnormal_vertex:Nv,displacementmap_pars_vertex:Ov,displacementmap_vertex:Bv,emissivemap_fragment:kv,emissivemap_pars_fragment:zv,colorspace_fragment:Gv,colorspace_pars_fragment:Hv,envmap_fragment:Vv,envmap_common_pars_fragment:Wv,envmap_pars_fragment:Xv,envmap_pars_vertex:Yv,envmap_physical_pars_fragment:ix,envmap_vertex:qv,fog_vertex:jv,fog_pars_vertex:Kv,fog_fragment:Zv,fog_pars_fragment:$v,gradientmap_pars_fragment:Jv,lightmap_pars_fragment:Qv,lights_lambert_fragment:ex,lights_lambert_pars_fragment:tx,lights_pars_begin:nx,lights_toon_fragment:rx,lights_toon_pars_fragment:sx,lights_phong_fragment:ax,lights_phong_pars_fragment:ox,lights_physical_fragment:lx,lights_physical_pars_fragment:cx,lights_fragment_begin:ux,lights_fragment_maps:hx,lights_fragment_end:fx,lightprobes_pars_fragment:dx,logdepthbuf_fragment:px,logdepthbuf_pars_fragment:mx,logdepthbuf_pars_vertex:gx,logdepthbuf_vertex:_x,map_fragment:vx,map_pars_fragment:xx,map_particle_fragment:Mx,map_particle_pars_fragment:Sx,metalnessmap_fragment:bx,metalnessmap_pars_fragment:yx,morphinstance_vertex:Tx,morphcolor_vertex:Ex,morphnormal_vertex:wx,morphtarget_pars_vertex:Ax,morphtarget_vertex:Rx,normal_fragment_begin:Cx,normal_fragment_maps:Px,normal_pars_fragment:Dx,normal_pars_vertex:Ux,normal_vertex:Lx,normalmap_pars_fragment:Ix,clearcoat_normal_fragment_begin:Fx,clearcoat_normal_fragment_maps:Nx,clearcoat_pars_fragment:Ox,iridescence_pars_fragment:Bx,opaque_fragment:kx,packing:zx,premultiplied_alpha_fragment:Gx,project_vertex:Hx,dithering_fragment:Vx,dithering_pars_fragment:Wx,roughnessmap_fragment:Xx,roughnessmap_pars_fragment:Yx,shadowmap_pars_fragment:qx,shadowmap_pars_vertex:jx,shadowmap_vertex:Kx,shadowmask_pars_fragment:Zx,skinbase_vertex:$x,skinning_pars_vertex:Jx,skinning_vertex:Qx,skinnormal_vertex:e1,specularmap_fragment:t1,specularmap_pars_fragment:n1,tonemapping_fragment:i1,tonemapping_pars_fragment:r1,transmission_fragment:s1,transmission_pars_fragment:a1,uv_pars_fragment:o1,uv_pars_vertex:l1,uv_vertex:c1,worldpos_vertex:u1,background_vert:h1,background_frag:f1,backgroundCube_vert:d1,backgroundCube_frag:p1,cube_vert:m1,cube_frag:g1,depth_vert:_1,depth_frag:v1,distance_vert:x1,distance_frag:M1,equirect_vert:S1,equirect_frag:b1,linedashed_vert:y1,linedashed_frag:T1,meshbasic_vert:E1,meshbasic_frag:w1,meshlambert_vert:A1,meshlambert_frag:R1,meshmatcap_vert:C1,meshmatcap_frag:P1,meshnormal_vert:D1,meshnormal_frag:U1,meshphong_vert:L1,meshphong_frag:I1,meshphysical_vert:F1,meshphysical_frag:N1,meshtoon_vert:O1,meshtoon_frag:B1,points_vert:k1,points_frag:z1,shadow_vert:G1,shadow_frag:H1,sprite_vert:V1,sprite_frag:W1},Be={common:{diffuse:{value:new lt(16777215)},opacity:{value:1},map:{value:null},mapTransform:{value:new nt},alphaMap:{value:null},alphaMapTransform:{value:new nt},alphaTest:{value:0}},specularmap:{specularMap:{value:null},specularMapTransform:{value:new nt}},envmap:{envMap:{value:null},envMapRotation:{value:new nt},reflectivity:{value:1},ior:{value:1.5},refractionRatio:{value:.98},dfgLUT:{value:null}},aomap:{aoMap:{value:null},aoMapIntensity:{value:1},aoMapTransform:{value:new nt}},lightmap:{lightMap:{value:null},lightMapIntensity:{value:1},lightMapTransform:{value:new nt}},bumpmap:{bumpMap:{value:null},bumpMapTransform:{value:new nt},bumpScale:{value:1}},normalmap:{normalMap:{value:null},normalMapTransform:{value:new nt},normalScale:{value:new We(1,1)}},displacementmap:{displacementMap:{value:null},displacementMapTransform:{value:new nt},displacementScale:{value:1},displacementBias:{value:0}},emissivemap:{emissiveMap:{value:null},emissiveMapTransform:{value:new nt}},metalnessmap:{metalnessMap:{value:null},metalnessMapTransform:{value:new nt}},roughnessmap:{roughnessMap:{value:null},roughnessMapTransform:{value:new nt}},gradientmap:{gradientMap:{value:null}},fog:{fogDensity:{value:25e-5},fogNear:{value:1},fogFar:{value:2e3},fogColor:{value:new lt(16777215)}},lights:{ambientLightColor:{value:[]},lightProbe:{value:[]},directionalLights:{value:[],properties:{direction:{},color:{}}},directionalLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},directionalShadowMatrix:{value:[]},spotLights:{value:[],properties:{color:{},position:{},direction:{},distance:{},coneCos:{},penumbraCos:{},decay:{}}},spotLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},spotLightMap:{value:[]},spotLightMatrix:{value:[]},pointLights:{value:[],properties:{color:{},position:{},decay:{},distance:{}}},pointLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{},shadowCameraNear:{},shadowCameraFar:{}}},pointShadowMatrix:{value:[]},hemisphereLights:{value:[],properties:{direction:{},skyColor:{},groundColor:{}}},rectAreaLights:{value:[],properties:{color:{},position:{},width:{},height:{}}},ltc_1:{value:null},ltc_2:{value:null},probesSH:{value:null},probesMin:{value:new X},probesMax:{value:new X},probesResolution:{value:new X}},points:{diffuse:{value:new lt(16777215)},opacity:{value:1},size:{value:1},scale:{value:1},map:{value:null},alphaMap:{value:null},alphaMapTransform:{value:new nt},alphaTest:{value:0},uvTransform:{value:new nt}},sprite:{diffuse:{value:new lt(16777215)},opacity:{value:1},center:{value:new We(.5,.5)},rotation:{value:0},map:{value:null},mapTransform:{value:new nt},alphaMap:{value:null},alphaMapTransform:{value:new nt},alphaTest:{value:0}}},bi={basic:{uniforms:Mn([Be.common,Be.specularmap,Be.envmap,Be.aomap,Be.lightmap,Be.fog]),vertexShader:it.meshbasic_vert,fragmentShader:it.meshbasic_frag},lambert:{uniforms:Mn([Be.common,Be.specularmap,Be.envmap,Be.aomap,Be.lightmap,Be.emissivemap,Be.bumpmap,Be.normalmap,Be.displacementmap,Be.fog,Be.lights,{emissive:{value:new lt(0)},envMapIntensity:{value:1}}]),vertexShader:it.meshlambert_vert,fragmentShader:it.meshlambert_frag},phong:{uniforms:Mn([Be.common,Be.specularmap,Be.envmap,Be.aomap,Be.lightmap,Be.emissivemap,Be.bumpmap,Be.normalmap,Be.displacementmap,Be.fog,Be.lights,{emissive:{value:new lt(0)},specular:{value:new lt(1118481)},shininess:{value:30},envMapIntensity:{value:1}}]),vertexShader:it.meshphong_vert,fragmentShader:it.meshphong_frag},standard:{uniforms:Mn([Be.common,Be.envmap,Be.aomap,Be.lightmap,Be.emissivemap,Be.bumpmap,Be.normalmap,Be.displacementmap,Be.roughnessmap,Be.metalnessmap,Be.fog,Be.lights,{emissive:{value:new lt(0)},roughness:{value:1},metalness:{value:0},envMapIntensity:{value:1}}]),vertexShader:it.meshphysical_vert,fragmentShader:it.meshphysical_frag},toon:{uniforms:Mn([Be.common,Be.aomap,Be.lightmap,Be.emissivemap,Be.bumpmap,Be.normalmap,Be.displacementmap,Be.gradientmap,Be.fog,Be.lights,{emissive:{value:new lt(0)}}]),vertexShader:it.meshtoon_vert,fragmentShader:it.meshtoon_frag},matcap:{uniforms:Mn([Be.common,Be.bumpmap,Be.normalmap,Be.displacementmap,Be.fog,{matcap:{value:null}}]),vertexShader:it.meshmatcap_vert,fragmentShader:it.meshmatcap_frag},points:{uniforms:Mn([Be.points,Be.fog]),vertexShader:it.points_vert,fragmentShader:it.points_frag},dashed:{uniforms:Mn([Be.common,Be.fog,{scale:{value:1},dashSize:{value:1},totalSize:{value:2}}]),vertexShader:it.linedashed_vert,fragmentShader:it.linedashed_frag},depth:{uniforms:Mn([Be.common,Be.displacementmap]),vertexShader:it.depth_vert,fragmentShader:it.depth_frag},normal:{uniforms:Mn([Be.common,Be.bumpmap,Be.normalmap,Be.displacementmap,{opacity:{value:1}}]),vertexShader:it.meshnormal_vert,fragmentShader:it.meshnormal_frag},sprite:{uniforms:Mn([Be.sprite,Be.fog]),vertexShader:it.sprite_vert,fragmentShader:it.sprite_frag},background:{uniforms:{uvTransform:{value:new nt},t2D:{value:null},backgroundIntensity:{value:1}},vertexShader:it.background_vert,fragmentShader:it.background_frag},backgroundCube:{uniforms:{envMap:{value:null},backgroundBlurriness:{value:0},backgroundIntensity:{value:1},backgroundRotation:{value:new nt}},vertexShader:it.backgroundCube_vert,fragmentShader:it.backgroundCube_frag},cube:{uniforms:{tCube:{value:null},tFlip:{value:-1},opacity:{value:1}},vertexShader:it.cube_vert,fragmentShader:it.cube_frag},equirect:{uniforms:{tEquirect:{value:null}},vertexShader:it.equirect_vert,fragmentShader:it.equirect_frag},distance:{uniforms:Mn([Be.common,Be.displacementmap,{referencePosition:{value:new X},nearDistance:{value:1},farDistance:{value:1e3}}]),vertexShader:it.distance_vert,fragmentShader:it.distance_frag},shadow:{uniforms:Mn([Be.lights,Be.fog,{color:{value:new lt(0)},opacity:{value:1}}]),vertexShader:it.shadow_vert,fragmentShader:it.shadow_frag}};bi.physical={uniforms:Mn([bi.standard.uniforms,{clearcoat:{value:0},clearcoatMap:{value:null},clearcoatMapTransform:{value:new nt},clearcoatNormalMap:{value:null},clearcoatNormalMapTransform:{value:new nt},clearcoatNormalScale:{value:new We(1,1)},clearcoatRoughness:{value:0},clearcoatRoughnessMap:{value:null},clearcoatRoughnessMapTransform:{value:new nt},dispersion:{value:0},iridescence:{value:0},iridescenceMap:{value:null},iridescenceMapTransform:{value:new nt},iridescenceIOR:{value:1.3},iridescenceThicknessMinimum:{value:100},iridescenceThicknessMaximum:{value:400},iridescenceThicknessMap:{value:null},iridescenceThicknessMapTransform:{value:new nt},sheen:{value:0},sheenColor:{value:new lt(0)},sheenColorMap:{value:null},sheenColorMapTransform:{value:new nt},sheenRoughness:{value:1},sheenRoughnessMap:{value:null},sheenRoughnessMapTransform:{value:new nt},transmission:{value:0},transmissionMap:{value:null},transmissionMapTransform:{value:new nt},transmissionSamplerSize:{value:new We},transmissionSamplerMap:{value:null},thickness:{value:0},thicknessMap:{value:null},thicknessMapTransform:{value:new nt},attenuationDistance:{value:0},attenuationColor:{value:new lt(0)},specularColor:{value:new lt(1,1,1)},specularColorMap:{value:null},specularColorMapTransform:{value:new nt},specularIntensity:{value:1},specularIntensityMap:{value:null},specularIntensityMapTransform:{value:new nt},anisotropyVector:{value:new We},anisotropyMap:{value:null},anisotropyMapTransform:{value:new nt}}]),vertexShader:it.meshphysical_vert,fragmentShader:it.meshphysical_frag};const Lo={r:0,b:0,g:0},X1=new Ot,Hm=new nt;Hm.set(-1,0,0,0,1,0,0,0,1);function Y1(n,e,t,r,i,s){const a=new lt(0);let o=i===!0?0:1,l,c,u=null,f=0,h=null;function d(M){let y=M.isScene===!0?M.background:null;if(y&&y.isTexture){const v=M.backgroundBlurriness>0;y=e.get(y,v)}return y}function m(M){let y=!1;const v=d(M);v===null?p(a,o):v&&v.isColor&&(p(v,1),y=!0);const S=n.xr.getEnvironmentBlendMode();S==="additive"?t.buffers.color.setClear(0,0,0,1,s):S==="alpha-blend"&&t.buffers.color.setClear(0,0,0,0,s),(n.autoClear||y)&&(t.buffers.depth.setTest(!0),t.buffers.depth.setMask(!0),t.buffers.color.setMask(!0),n.clear(n.autoClearColor,n.autoClearDepth,n.autoClearStencil))}function g(M,y){const v=d(y);v&&(v.isCubeTexture||v.mapping===Al)?(c===void 0&&(c=new Wn(new Ka(1,1,1),new an({name:"BackgroundCubeMaterial",uniforms:zs(bi.backgroundCube.uniforms),vertexShader:bi.backgroundCube.vertexShader,fragmentShader:bi.backgroundCube.fragmentShader,side:sn,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),c.geometry.deleteAttribute("normal"),c.geometry.deleteAttribute("uv"),c.onBeforeRender=function(S,b,E){this.matrixWorld.copyPosition(E.matrixWorld)},Object.defineProperty(c.material,"envMap",{get:function(){return this.uniforms.envMap.value}}),r.update(c)),c.material.uniforms.envMap.value=v,c.material.uniforms.backgroundBlurriness.value=y.backgroundBlurriness,c.material.uniforms.backgroundIntensity.value=y.backgroundIntensity,c.material.uniforms.backgroundRotation.value.setFromMatrix4(X1.makeRotationFromEuler(y.backgroundRotation)).transpose(),v.isCubeTexture&&v.isRenderTargetTexture===!1&&c.material.uniforms.backgroundRotation.value.premultiply(Hm),c.material.toneMapped=ut.getTransfer(v.colorSpace)!==xt,(u!==v||f!==v.version||h!==n.toneMapping)&&(c.material.needsUpdate=!0,u=v,f=v.version,h=n.toneMapping),c.layers.enableAll(),M.unshift(c,c.geometry,c.material,0,0,null)):v&&v.isTexture&&(l===void 0&&(l=new Wn(new $r(2,2),new an({name:"BackgroundMaterial",uniforms:zs(bi.background.uniforms),vertexShader:bi.background.vertexShader,fragmentShader:bi.background.fragmentShader,side:Xi,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),l.geometry.deleteAttribute("normal"),Object.defineProperty(l.material,"map",{get:function(){return this.uniforms.t2D.value}}),r.update(l)),l.material.uniforms.t2D.value=v,l.material.uniforms.backgroundIntensity.value=y.backgroundIntensity,l.material.toneMapped=ut.getTransfer(v.colorSpace)!==xt,v.matrixAutoUpdate===!0&&v.updateMatrix(),l.material.uniforms.uvTransform.value.copy(v.matrix),(u!==v||f!==v.version||h!==n.toneMapping)&&(l.material.needsUpdate=!0,u=v,f=v.version,h=n.toneMapping),l.layers.enableAll(),M.unshift(l,l.geometry,l.material,0,0,null))}function p(M,y){M.getRGB(Lo,Nm(n)),t.buffers.color.setClear(Lo.r,Lo.g,Lo.b,y,s)}function _(){c!==void 0&&(c.geometry.dispose(),c.material.dispose(),c=void 0),l!==void 0&&(l.geometry.dispose(),l.material.dispose(),l=void 0)}return{getClearColor:function(){return a},setClearColor:function(M,y=1){a.set(M),o=y,p(a,o)},getClearAlpha:function(){return o},setClearAlpha:function(M){o=M,p(a,o)},render:m,addToRenderList:g,dispose:_}}function q1(n,e){const t=n.getParameter(n.MAX_VERTEX_ATTRIBS),r={},i=h(null);let s=i,a=!1;function o(L,A,U,P,I){let F=!1;const O=f(L,P,U,A);s!==O&&(s=O,c(s.object)),F=d(L,P,U,I),F&&m(L,P,U,I),I!==null&&e.update(I,n.ELEMENT_ARRAY_BUFFER),(F||a)&&(a=!1,v(L,A,U,P),I!==null&&n.bindBuffer(n.ELEMENT_ARRAY_BUFFER,e.get(I).buffer))}function l(){return n.createVertexArray()}function c(L){return n.bindVertexArray(L)}function u(L){return n.deleteVertexArray(L)}function f(L,A,U,P){const I=P.wireframe===!0;let F=r[A.id];F===void 0&&(F={},r[A.id]=F);const O=L.isInstancedMesh===!0?L.id:0;let q=F[O];q===void 0&&(q={},F[O]=q);let z=q[U.id];z===void 0&&(z={},q[U.id]=z);let k=z[I];return k===void 0&&(k=h(l()),z[I]=k),k}function h(L){const A=[],U=[],P=[];for(let I=0;I<t;I++)A[I]=0,U[I]=0,P[I]=0;return{geometry:null,program:null,wireframe:!1,newAttributes:A,enabledAttributes:U,attributeDivisors:P,object:L,attributes:{},index:null}}function d(L,A,U,P){const I=s.attributes,F=A.attributes;let O=0;const q=U.getAttributes();for(const z in q)if(q[z].location>=0){const N=I[z];let G=F[z];if(G===void 0&&(z==="instanceMatrix"&&L.instanceMatrix&&(G=L.instanceMatrix),z==="instanceColor"&&L.instanceColor&&(G=L.instanceColor)),N===void 0||N.attribute!==G||G&&N.data!==G.data)return!0;O++}return s.attributesNum!==O||s.index!==P}function m(L,A,U,P){const I={},F=A.attributes;let O=0;const q=U.getAttributes();for(const z in q)if(q[z].location>=0){let N=F[z];N===void 0&&(z==="instanceMatrix"&&L.instanceMatrix&&(N=L.instanceMatrix),z==="instanceColor"&&L.instanceColor&&(N=L.instanceColor));const G={};G.attribute=N,N&&N.data&&(G.data=N.data),I[z]=G,O++}s.attributes=I,s.attributesNum=O,s.index=P}function g(){const L=s.newAttributes;for(let A=0,U=L.length;A<U;A++)L[A]=0}function p(L){_(L,0)}function _(L,A){const U=s.newAttributes,P=s.enabledAttributes,I=s.attributeDivisors;U[L]=1,P[L]===0&&(n.enableVertexAttribArray(L),P[L]=1),I[L]!==A&&(n.vertexAttribDivisor(L,A),I[L]=A)}function M(){const L=s.newAttributes,A=s.enabledAttributes;for(let U=0,P=A.length;U<P;U++)A[U]!==L[U]&&(n.disableVertexAttribArray(U),A[U]=0)}function y(L,A,U,P,I,F,O){O===!0?n.vertexAttribIPointer(L,A,U,I,F):n.vertexAttribPointer(L,A,U,P,I,F)}function v(L,A,U,P){g();const I=P.attributes,F=U.getAttributes(),O=A.defaultAttributeValues;for(const q in F){const z=F[q];if(z.location>=0){let k=I[q];if(k===void 0&&(q==="instanceMatrix"&&L.instanceMatrix&&(k=L.instanceMatrix),q==="instanceColor"&&L.instanceColor&&(k=L.instanceColor)),k!==void 0){const N=k.normalized,G=k.itemSize,K=e.get(k);if(K===void 0)continue;const J=K.buffer,j=K.type,V=K.bytesPerElement,Y=j===n.INT||j===n.UNSIGNED_INT||k.gpuType===Hh;if(k.isInterleavedBufferAttribute){const Z=k.data,fe=Z.stride,_e=k.offset;if(Z.isInstancedInterleavedBuffer){for(let le=0;le<z.locationSize;le++)_(z.location+le,Z.meshPerAttribute);L.isInstancedMesh!==!0&&P._maxInstanceCount===void 0&&(P._maxInstanceCount=Z.meshPerAttribute*Z.count)}else for(let le=0;le<z.locationSize;le++)p(z.location+le);n.bindBuffer(n.ARRAY_BUFFER,J);for(let le=0;le<z.locationSize;le++)y(z.location+le,G/z.locationSize,j,N,fe*V,(_e+G/z.locationSize*le)*V,Y)}else{if(k.isInstancedBufferAttribute){for(let Z=0;Z<z.locationSize;Z++)_(z.location+Z,k.meshPerAttribute);L.isInstancedMesh!==!0&&P._maxInstanceCount===void 0&&(P._maxInstanceCount=k.meshPerAttribute*k.count)}else for(let Z=0;Z<z.locationSize;Z++)p(z.location+Z);n.bindBuffer(n.ARRAY_BUFFER,J);for(let Z=0;Z<z.locationSize;Z++)y(z.location+Z,G/z.locationSize,j,N,G*V,G/z.locationSize*Z*V,Y)}}else if(O!==void 0){const N=O[q];if(N!==void 0)switch(N.length){case 2:n.vertexAttrib2fv(z.location,N);break;case 3:n.vertexAttrib3fv(z.location,N);break;case 4:n.vertexAttrib4fv(z.location,N);break;default:n.vertexAttrib1fv(z.location,N)}}}}M()}function S(){w();for(const L in r){const A=r[L];for(const U in A){const P=A[U];for(const I in P){const F=P[I];for(const O in F)u(F[O].object),delete F[O];delete P[I]}}delete r[L]}}function b(L){if(r[L.id]===void 0)return;const A=r[L.id];for(const U in A){const P=A[U];for(const I in P){const F=P[I];for(const O in F)u(F[O].object),delete F[O];delete P[I]}}delete r[L.id]}function E(L){for(const A in r){const U=r[A];for(const P in U){const I=U[P];if(I[L.id]===void 0)continue;const F=I[L.id];for(const O in F)u(F[O].object),delete F[O];delete I[L.id]}}}function x(L){for(const A in r){const U=r[A],P=L.isInstancedMesh===!0?L.id:0,I=U[P];if(I!==void 0){for(const F in I){const O=I[F];for(const q in O)u(O[q].object),delete O[q];delete I[F]}delete U[P],Object.keys(U).length===0&&delete r[A]}}}function w(){R(),a=!0,s!==i&&(s=i,c(s.object))}function R(){i.geometry=null,i.program=null,i.wireframe=!1}return{setup:o,reset:w,resetDefaultState:R,dispose:S,releaseStatesOfGeometry:b,releaseStatesOfObject:x,releaseStatesOfProgram:E,initAttributes:g,enableAttribute:p,disableUnusedAttributes:M}}function j1(n,e,t){let r;function i(l){r=l}function s(l,c){n.drawArrays(r,l,c),t.update(c,r,1)}function a(l,c,u){u!==0&&(n.drawArraysInstanced(r,l,c,u),t.update(c,r,u))}function o(l,c,u){if(u===0)return;e.get("WEBGL_multi_draw").multiDrawArraysWEBGL(r,l,0,c,0,u);let h=0;for(let d=0;d<u;d++)h+=c[d];t.update(h,r,1)}this.setMode=i,this.render=s,this.renderInstances=a,this.renderMultiDraw=o}function K1(n,e,t,r){let i;function s(){if(i!==void 0)return i;if(e.has("EXT_texture_filter_anisotropic")===!0){const E=e.get("EXT_texture_filter_anisotropic");i=n.getParameter(E.MAX_TEXTURE_MAX_ANISOTROPY_EXT)}else i=0;return i}function a(E){return!(E!==ci&&r.convert(E)!==n.getParameter(n.IMPLEMENTATION_COLOR_READ_FORMAT))}function o(E){const x=E===Yi&&(e.has("EXT_color_buffer_half_float")||e.has("EXT_color_buffer_float"));return!(E!==Yt&&r.convert(E)!==n.getParameter(n.IMPLEMENTATION_COLOR_READ_TYPE)&&E!==li&&!x)}function l(E){if(E==="highp"){if(n.getShaderPrecisionFormat(n.VERTEX_SHADER,n.HIGH_FLOAT).precision>0&&n.getShaderPrecisionFormat(n.FRAGMENT_SHADER,n.HIGH_FLOAT).precision>0)return"highp";E="mediump"}return E==="mediump"&&n.getShaderPrecisionFormat(n.VERTEX_SHADER,n.MEDIUM_FLOAT).precision>0&&n.getShaderPrecisionFormat(n.FRAGMENT_SHADER,n.MEDIUM_FLOAT).precision>0?"mediump":"lowp"}let c=t.precision!==void 0?t.precision:"highp";const u=l(c);u!==c&&($e("WebGLRenderer:",c,"not supported, using",u,"instead."),c=u);const f=t.logarithmicDepthBuffer===!0,h=t.reversedDepthBuffer===!0&&e.has("EXT_clip_control");t.reversedDepthBuffer===!0&&h===!1&&$e("WebGLRenderer: Unable to use reversed depth buffer due to missing EXT_clip_control extension. Fallback to default depth buffer.");const d=n.getParameter(n.MAX_TEXTURE_IMAGE_UNITS),m=n.getParameter(n.MAX_VERTEX_TEXTURE_IMAGE_UNITS),g=n.getParameter(n.MAX_TEXTURE_SIZE),p=n.getParameter(n.MAX_CUBE_MAP_TEXTURE_SIZE),_=n.getParameter(n.MAX_VERTEX_ATTRIBS),M=n.getParameter(n.MAX_VERTEX_UNIFORM_VECTORS),y=n.getParameter(n.MAX_VARYING_VECTORS),v=n.getParameter(n.MAX_FRAGMENT_UNIFORM_VECTORS),S=n.getParameter(n.MAX_SAMPLES),b=n.getParameter(n.SAMPLES);return{isWebGL2:!0,getMaxAnisotropy:s,getMaxPrecision:l,textureFormatReadable:a,textureTypeReadable:o,precision:c,logarithmicDepthBuffer:f,reversedDepthBuffer:h,maxTextures:d,maxVertexTextures:m,maxTextureSize:g,maxCubemapSize:p,maxAttributes:_,maxVertexUniforms:M,maxVaryings:y,maxFragmentUniforms:v,maxSamples:S,samples:b}}function Z1(n){const e=this;let t=null,r=0,i=!1,s=!1;const a=new lr,o=new nt,l={value:null,needsUpdate:!1};this.uniform=l,this.numPlanes=0,this.numIntersection=0,this.init=function(f,h){const d=f.length!==0||h||r!==0||i;return i=h,r=f.length,d},this.beginShadows=function(){s=!0,u(null)},this.endShadows=function(){s=!1},this.setGlobalState=function(f,h){t=u(f,h,0)},this.setState=function(f,h,d){const m=f.clippingPlanes,g=f.clipIntersection,p=f.clipShadows,_=n.get(f);if(!i||m===null||m.length===0||s&&!p)s?u(null):c();else{const M=s?0:r,y=M*4;let v=_.clippingState||null;l.value=v,v=u(m,h,y,d);for(let S=0;S!==y;++S)v[S]=t[S];_.clippingState=v,this.numIntersection=g?this.numPlanes:0,this.numPlanes+=M}};function c(){l.value!==t&&(l.value=t,l.needsUpdate=r>0),e.numPlanes=r,e.numIntersection=0}function u(f,h,d,m){const g=f!==null?f.length:0;let p=null;if(g!==0){if(p=l.value,m!==!0||p===null){const _=d+g*4,M=h.matrixWorldInverse;o.getNormalMatrix(M),(p===null||p.length<_)&&(p=new Float32Array(_));for(let y=0,v=d;y!==g;++y,v+=4)a.copy(f[y]).applyMatrix4(M,o),a.normal.toArray(p,v),p[v+3]=a.constant}l.value=p,l.needsUpdate=!0}return e.numPlanes=g,e.numIntersection=0,p}}const ur=4,Pd=[.125,.215,.35,.446,.526,.582],Or=20,$1=256,va=new Qh,Dd=new lt;let Pc=null,Dc=0,Uc=0,Lc=!1;const J1=new X;class Ud{constructor(e){this._renderer=e,this._pingPongRenderTarget=null,this._lodMax=0,this._cubeSize=0,this._sizeLods=[],this._sigmas=[],this._lodMeshes=[],this._backgroundBox=null,this._cubemapMaterial=null,this._equirectMaterial=null,this._blurMaterial=null,this._ggxMaterial=null}fromScene(e,t=0,r=.1,i=100,s={}){const{size:a=256,position:o=J1}=s;Pc=this._renderer.getRenderTarget(),Dc=this._renderer.getActiveCubeFace(),Uc=this._renderer.getActiveMipmapLevel(),Lc=this._renderer.xr.enabled,this._renderer.xr.enabled=!1,this._setSize(a);const l=this._allocateTargets();return l.depthBuffer=!0,this._sceneToCubeUV(e,r,i,l,o),t>0&&this._blur(l,0,0,t),this._applyPMREM(l),this._cleanup(l),l}fromEquirectangular(e,t=null){return this._fromTexture(e,t)}fromCubemap(e,t=null){return this._fromTexture(e,t)}compileCubemapShader(){this._cubemapMaterial===null&&(this._cubemapMaterial=Fd(),this._compileMaterial(this._cubemapMaterial))}compileEquirectangularShader(){this._equirectMaterial===null&&(this._equirectMaterial=Id(),this._compileMaterial(this._equirectMaterial))}dispose(){this._dispose(),this._cubemapMaterial!==null&&this._cubemapMaterial.dispose(),this._equirectMaterial!==null&&this._equirectMaterial.dispose(),this._backgroundBox!==null&&(this._backgroundBox.geometry.dispose(),this._backgroundBox.material.dispose())}_setSize(e){this._lodMax=Math.floor(Math.log2(e)),this._cubeSize=Math.pow(2,this._lodMax)}_dispose(){this._blurMaterial!==null&&this._blurMaterial.dispose(),this._ggxMaterial!==null&&this._ggxMaterial.dispose(),this._pingPongRenderTarget!==null&&this._pingPongRenderTarget.dispose();for(let e=0;e<this._lodMeshes.length;e++)this._lodMeshes[e].geometry.dispose()}_cleanup(e){this._renderer.setRenderTarget(Pc,Dc,Uc),this._renderer.xr.enabled=Lc,e.scissorTest=!1,ys(e,0,0,e.width,e.height)}_fromTexture(e,t){e.mapping===jr||e.mapping===Os?this._setSize(e.image.length===0?16:e.image[0].width||e.image[0].image.width):this._setSize(e.image.width/4),Pc=this._renderer.getRenderTarget(),Dc=this._renderer.getActiveCubeFace(),Uc=this._renderer.getActiveMipmapLevel(),Lc=this._renderer.xr.enabled,this._renderer.xr.enabled=!1;const r=t||this._allocateTargets();return this._textureToCubeUV(e,r),this._applyPMREM(r),this._cleanup(r),r}_allocateTargets(){const e=3*Math.max(this._cubeSize,112),t=4*this._cubeSize,r={magFilter:zt,minFilter:zt,generateMipmaps:!1,type:Yi,format:ci,colorSpace:ks,depthBuffer:!1},i=Ld(e,t,r);if(this._pingPongRenderTarget===null||this._pingPongRenderTarget.width!==e||this._pingPongRenderTarget.height!==t){this._pingPongRenderTarget!==null&&this._dispose(),this._pingPongRenderTarget=Ld(e,t,r);const{_lodMax:s}=this;({lodMeshes:this._lodMeshes,sizeLods:this._sizeLods,sigmas:this._sigmas}=Q1(s)),this._blurMaterial=tM(s,e,t),this._ggxMaterial=eM(s,e,t)}return i}_compileMaterial(e){const t=new Wn(new Dt,e);this._renderer.compile(t,va)}_sceneToCubeUV(e,t,r,i,s){const l=new kn(90,1,t,r),c=[1,-1,1,1,1,1],u=[1,1,1,-1,-1,-1],f=this._renderer,h=f.autoClear,d=f.toneMapping;f.getClearColor(Dd),f.toneMapping=Pi,f.autoClear=!1,f.state.buffers.depth.getReversed()&&(f.setRenderTarget(i),f.clearDepth(),f.setRenderTarget(null)),this._backgroundBox===null&&(this._backgroundBox=new Wn(new Ka,new $h({name:"PMREM.Background",side:sn,depthWrite:!1,depthTest:!1})));const g=this._backgroundBox,p=g.material;let _=!1;const M=e.background;M?M.isColor&&(p.color.copy(M),e.background=null,_=!0):(p.color.copy(Dd),_=!0);for(let y=0;y<6;y++){const v=y%3;v===0?(l.up.set(0,c[y],0),l.position.set(s.x,s.y,s.z),l.lookAt(s.x+u[y],s.y,s.z)):v===1?(l.up.set(0,0,c[y]),l.position.set(s.x,s.y,s.z),l.lookAt(s.x,s.y+u[y],s.z)):(l.up.set(0,c[y],0),l.position.set(s.x,s.y,s.z),l.lookAt(s.x,s.y,s.z+u[y]));const S=this._cubeSize;ys(i,v*S,y>2?S:0,S,S),f.setRenderTarget(i),_&&f.render(g,l),f.render(e,l)}f.toneMapping=d,f.autoClear=h,e.background=M}_textureToCubeUV(e,t){const r=this._renderer,i=e.mapping===jr||e.mapping===Os;i?(this._cubemapMaterial===null&&(this._cubemapMaterial=Fd()),this._cubemapMaterial.uniforms.flipEnvMap.value=e.isRenderTargetTexture===!1?-1:1):this._equirectMaterial===null&&(this._equirectMaterial=Id());const s=i?this._cubemapMaterial:this._equirectMaterial,a=this._lodMeshes[0];a.material=s;const o=s.uniforms;o.envMap.value=e;const l=this._cubeSize;ys(t,0,0,3*l,2*l),r.setRenderTarget(t),r.render(a,va)}_applyPMREM(e){const t=this._renderer,r=t.autoClear;t.autoClear=!1;const i=this._lodMeshes.length;for(let s=1;s<i;s++)this._applyGGXFilter(e,s-1,s);t.autoClear=r}_applyGGXFilter(e,t,r){const i=this._renderer,s=this._pingPongRenderTarget,a=this._ggxMaterial,o=this._lodMeshes[r];o.material=a;const l=a.uniforms,c=r/(this._lodMeshes.length-1),u=t/(this._lodMeshes.length-1),f=Math.sqrt(c*c-u*u),h=0+c*1.25,d=f*h,{_lodMax:m}=this,g=this._sizeLods[r],p=3*g*(r>m-ur?r-m+ur:0),_=4*(this._cubeSize-g);l.envMap.value=e.texture,l.roughness.value=d,l.mipInt.value=m-t,ys(s,p,_,3*g,2*g),i.setRenderTarget(s),i.render(o,va),l.envMap.value=s.texture,l.roughness.value=0,l.mipInt.value=m-r,ys(e,p,_,3*g,2*g),i.setRenderTarget(e),i.render(o,va)}_blur(e,t,r,i,s){const a=this._pingPongRenderTarget;this._halfBlur(e,a,t,r,i,"latitudinal",s),this._halfBlur(a,e,r,r,i,"longitudinal",s)}_halfBlur(e,t,r,i,s,a,o){const l=this._renderer,c=this._blurMaterial;a!=="latitudinal"&&a!=="longitudinal"&&ft("blur direction must be either latitudinal or longitudinal!");const u=3,f=this._lodMeshes[i];f.material=c;const h=c.uniforms,d=this._sizeLods[r]-1,m=isFinite(s)?Math.PI/(2*d):2*Math.PI/(2*Or-1),g=s/m,p=isFinite(s)?1+Math.floor(u*g):Or;p>Or&&$e(`sigmaRadians, ${s}, is too large and will clip, as it requested ${p} samples when the maximum is set to ${Or}`);const _=[];let M=0;for(let E=0;E<Or;++E){const x=E/g,w=Math.exp(-x*x/2);_.push(w),E===0?M+=w:E<p&&(M+=2*w)}for(let E=0;E<_.length;E++)_[E]=_[E]/M;h.envMap.value=e.texture,h.samples.value=p,h.weights.value=_,h.latitudinal.value=a==="latitudinal",o&&(h.poleAxis.value=o);const{_lodMax:y}=this;h.dTheta.value=m,h.mipInt.value=y-r;const v=this._sizeLods[i],S=3*v*(i>y-ur?i-y+ur:0),b=4*(this._cubeSize-v);ys(t,S,b,3*v,2*v),l.setRenderTarget(t),l.render(f,va)}}function Q1(n){const e=[],t=[],r=[];let i=n;const s=n-ur+1+Pd.length;for(let a=0;a<s;a++){const o=Math.pow(2,i);e.push(o);let l=1/o;a>n-ur?l=Pd[a-n+ur-1]:a===0&&(l=0),t.push(l);const c=1/(o-2),u=-c,f=1+c,h=[u,u,f,u,f,f,u,u,f,f,u,f],d=6,m=6,g=3,p=2,_=1,M=new Float32Array(g*m*d),y=new Float32Array(p*m*d),v=new Float32Array(_*m*d);for(let b=0;b<d;b++){const E=b%3*2/3-1,x=b>2?0:-1,w=[E,x,0,E+2/3,x,0,E+2/3,x+1,0,E,x,0,E+2/3,x+1,0,E,x+1,0];M.set(w,g*m*b),y.set(h,p*m*b);const R=[b,b,b,b,b,b];v.set(R,_*m*b)}const S=new Dt;S.setAttribute("position",new kt(M,g)),S.setAttribute("uv",new kt(y,p)),S.setAttribute("faceIndex",new kt(v,_)),r.push(new Wn(S,null)),i>ur&&i--}return{lodMeshes:r,sizeLods:e,sigmas:t}}function Ld(n,e,t){const r=new $t(n,e,t);return r.texture.mapping=Al,r.texture.name="PMREM.cubeUv",r.scissorTest=!0,r}function ys(n,e,t,r,i){n.viewport.set(e,t,r,i),n.scissor.set(e,t,r,i)}function eM(n,e,t){return new an({name:"PMREMGGXConvolution",defines:{GGX_SAMPLES:$1,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/t,CUBEUV_MAX_MIP:`${n}.0`},uniforms:{envMap:{value:null},roughness:{value:0},mipInt:{value:0}},vertexShader:Cl(),fragmentShader:`

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
		`,blending:Sn,depthTest:!1,depthWrite:!1})}function tM(n,e,t){const r=new Float32Array(Or),i=new X(0,1,0);return new an({name:"SphericalGaussianBlur",defines:{n:Or,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/t,CUBEUV_MAX_MIP:`${n}.0`},uniforms:{envMap:{value:null},samples:{value:1},weights:{value:r},latitudinal:{value:!1},dTheta:{value:0},mipInt:{value:0},poleAxis:{value:i}},vertexShader:Cl(),fragmentShader:`

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
		`,blending:Sn,depthTest:!1,depthWrite:!1})}function Id(){return new an({name:"EquirectangularToCubeUV",uniforms:{envMap:{value:null}},vertexShader:Cl(),fragmentShader:`

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
		`,blending:Sn,depthTest:!1,depthWrite:!1})}function Fd(){return new an({name:"CubemapToCubeUV",uniforms:{envMap:{value:null},flipEnvMap:{value:-1}},vertexShader:Cl(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			uniform float flipEnvMap;

			varying vec3 vOutputDirection;

			uniform samplerCube envMap;

			void main() {

				gl_FragColor = textureCube( envMap, vec3( flipEnvMap * vOutputDirection.x, vOutputDirection.yz ) );

			}
		`,blending:Sn,depthTest:!1,depthWrite:!1})}function Cl(){return`

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
	`}class Vm extends $t{constructor(e=1,t={}){super(e,e,t),this.isWebGLCubeRenderTarget=!0;const r={width:e,height:e,depth:1},i=[r,r,r,r,r,r];this.texture=new Im(i),this._setTextureOptions(t),this.texture.isRenderTargetTexture=!0}fromEquirectangularTexture(e,t){this.texture.type=t.type,this.texture.colorSpace=t.colorSpace,this.texture.generateMipmaps=t.generateMipmaps,this.texture.minFilter=t.minFilter,this.texture.magFilter=t.magFilter;const r={uniforms:{tEquirect:{value:null}},vertexShader:`

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
			`},i=new Ka(5,5,5),s=new an({name:"CubemapFromEquirect",uniforms:zs(r.uniforms),vertexShader:r.vertexShader,fragmentShader:r.fragmentShader,side:sn,blending:Sn});s.uniforms.tEquirect.value=t;const a=new Wn(i,s),o=t.minFilter;return t.minFilter===Br&&(t.minFilter=zt),new sv(1,10,this).update(e,a),t.minFilter=o,a.geometry.dispose(),a.material.dispose(),this}clear(e,t=!0,r=!0,i=!0){const s=e.getRenderTarget();for(let a=0;a<6;a++)e.setRenderTarget(this,a),e.clear(t,r,i);e.setRenderTarget(s)}}function nM(n){let e=new WeakMap,t=new WeakMap,r=null;function i(h,d=!1){return h==null?null:d?a(h):s(h)}function s(h){if(h&&h.isTexture){const d=h.mapping;if(d===tc||d===nc)if(e.has(h)){const m=e.get(h).texture;return o(m,h.mapping)}else{const m=h.image;if(m&&m.height>0){const g=new Vm(m.height);return g.fromEquirectangularTexture(n,h),e.set(h,g),h.addEventListener("dispose",c),o(g.texture,h.mapping)}else return null}}return h}function a(h){if(h&&h.isTexture){const d=h.mapping,m=d===tc||d===nc,g=d===jr||d===Os;if(m||g){let p=t.get(h);const _=p!==void 0?p.texture.pmremVersion:0;if(h.isRenderTargetTexture&&h.pmremVersion!==_)return r===null&&(r=new Ud(n)),p=m?r.fromEquirectangular(h,p):r.fromCubemap(h,p),p.texture.pmremVersion=h.pmremVersion,t.set(h,p),p.texture;if(p!==void 0)return p.texture;{const M=h.image;return m&&M&&M.height>0||g&&M&&l(M)?(r===null&&(r=new Ud(n)),p=m?r.fromEquirectangular(h):r.fromCubemap(h),p.texture.pmremVersion=h.pmremVersion,t.set(h,p),h.addEventListener("dispose",u),p.texture):null}}}return h}function o(h,d){return d===tc?h.mapping=jr:d===nc&&(h.mapping=Os),h}function l(h){let d=0;const m=6;for(let g=0;g<m;g++)h[g]!==void 0&&d++;return d===m}function c(h){const d=h.target;d.removeEventListener("dispose",c);const m=e.get(d);m!==void 0&&(e.delete(d),m.dispose())}function u(h){const d=h.target;d.removeEventListener("dispose",u);const m=t.get(d);m!==void 0&&(t.delete(d),m.dispose())}function f(){e=new WeakMap,t=new WeakMap,r!==null&&(r.dispose(),r=null)}return{get:i,dispose:f}}function iM(n){const e={};function t(r){if(e[r]!==void 0)return e[r];const i=n.getExtension(r);return e[r]=i,i}return{has:function(r){return t(r)!==null},init:function(){t("EXT_color_buffer_float"),t("WEBGL_clip_cull_distance"),t("OES_texture_float_linear"),t("EXT_color_buffer_half_float"),t("WEBGL_multisampled_render_to_texture"),t("WEBGL_render_shared_exponent")},get:function(r){const i=t(r);return i===null&&lh("WebGLRenderer: "+r+" extension not supported."),i}}}function rM(n,e,t,r){const i={},s=new WeakMap;function a(f){const h=f.target;h.index!==null&&e.remove(h.index);for(const m in h.attributes)e.remove(h.attributes[m]);h.removeEventListener("dispose",a),delete i[h.id];const d=s.get(h);d&&(e.remove(d),s.delete(h)),r.releaseStatesOfGeometry(h),h.isInstancedBufferGeometry===!0&&delete h._maxInstanceCount,t.memory.geometries--}function o(f,h){return i[h.id]===!0||(h.addEventListener("dispose",a),i[h.id]=!0,t.memory.geometries++),h}function l(f){const h=f.attributes;for(const d in h)e.update(h[d],n.ARRAY_BUFFER)}function c(f){const h=[],d=f.index,m=f.attributes.position;let g=0;if(m===void 0)return;if(d!==null){const M=d.array;g=d.version;for(let y=0,v=M.length;y<v;y+=3){const S=M[y+0],b=M[y+1],E=M[y+2];h.push(S,b,b,E,E,S)}}else{const M=m.array;g=m.version;for(let y=0,v=M.length/3-1;y<v;y+=3){const S=y+0,b=y+1,E=y+2;h.push(S,b,b,E,E,S)}}const p=new(m.count>=65535?Dm:Pm)(h,1);p.version=g;const _=s.get(f);_&&e.remove(_),s.set(f,p)}function u(f){const h=s.get(f);if(h){const d=f.index;d!==null&&h.version<d.version&&c(f)}else c(f);return s.get(f)}return{get:o,update:l,getWireframeAttribute:u}}function sM(n,e,t){let r;function i(f){r=f}let s,a;function o(f){s=f.type,a=f.bytesPerElement}function l(f,h){n.drawElements(r,h,s,f*a),t.update(h,r,1)}function c(f,h,d){d!==0&&(n.drawElementsInstanced(r,h,s,f*a,d),t.update(h,r,d))}function u(f,h,d){if(d===0)return;e.get("WEBGL_multi_draw").multiDrawElementsWEBGL(r,h,0,s,f,0,d);let g=0;for(let p=0;p<d;p++)g+=h[p];t.update(g,r,1)}this.setMode=i,this.setIndex=o,this.render=l,this.renderInstances=c,this.renderMultiDraw=u}function aM(n){const e={geometries:0,textures:0},t={frame:0,calls:0,triangles:0,points:0,lines:0};function r(s,a,o){switch(t.calls++,a){case n.TRIANGLES:t.triangles+=o*(s/3);break;case n.LINES:t.lines+=o*(s/2);break;case n.LINE_STRIP:t.lines+=o*(s-1);break;case n.LINE_LOOP:t.lines+=o*s;break;case n.POINTS:t.points+=o*s;break;default:ft("WebGLInfo: Unknown draw mode:",a);break}}function i(){t.calls=0,t.triangles=0,t.points=0,t.lines=0}return{memory:e,render:t,programs:null,autoReset:!0,reset:i,update:r}}function oM(n,e,t){const r=new WeakMap,i=new Ct;function s(a,o,l){const c=a.morphTargetInfluences,u=o.morphAttributes.position||o.morphAttributes.normal||o.morphAttributes.color,f=u!==void 0?u.length:0;let h=r.get(o);if(h===void 0||h.count!==f){let w=function(){E.dispose(),r.delete(o),o.removeEventListener("dispose",w)};h!==void 0&&h.texture.dispose();const d=o.morphAttributes.position!==void 0,m=o.morphAttributes.normal!==void 0,g=o.morphAttributes.color!==void 0,p=o.morphAttributes.position||[],_=o.morphAttributes.normal||[],M=o.morphAttributes.color||[];let y=0;d===!0&&(y=1),m===!0&&(y=2),g===!0&&(y=3);let v=o.attributes.position.count*y,S=1;v>e.maxTextureSize&&(S=Math.ceil(v/e.maxTextureSize),v=e.maxTextureSize);const b=new Float32Array(v*S*4*f),E=new Am(b,v,S,f);E.type=li,E.needsUpdate=!0;const x=y*4;for(let R=0;R<f;R++){const L=p[R],A=_[R],U=M[R],P=v*S*4*R;for(let I=0;I<L.count;I++){const F=I*x;d===!0&&(i.fromBufferAttribute(L,I),b[P+F+0]=i.x,b[P+F+1]=i.y,b[P+F+2]=i.z,b[P+F+3]=0),m===!0&&(i.fromBufferAttribute(A,I),b[P+F+4]=i.x,b[P+F+5]=i.y,b[P+F+6]=i.z,b[P+F+7]=0),g===!0&&(i.fromBufferAttribute(U,I),b[P+F+8]=i.x,b[P+F+9]=i.y,b[P+F+10]=i.z,b[P+F+11]=U.itemSize===4?i.w:1)}}h={count:f,texture:E,size:new We(v,S)},r.set(o,h),o.addEventListener("dispose",w)}if(a.isInstancedMesh===!0&&a.morphTexture!==null)l.getUniforms().setValue(n,"morphTexture",a.morphTexture,t);else{let d=0;for(let g=0;g<c.length;g++)d+=c[g];const m=o.morphTargetsRelative?1:1-d;l.getUniforms().setValue(n,"morphTargetBaseInfluence",m),l.getUniforms().setValue(n,"morphTargetInfluences",c)}l.getUniforms().setValue(n,"morphTargetsTexture",h.texture,t),l.getUniforms().setValue(n,"morphTargetsTextureSize",h.size)}return{update:s}}function lM(n,e,t,r,i){let s=new WeakMap;function a(c){const u=i.render.frame,f=c.geometry,h=e.get(c,f);if(s.get(h)!==u&&(e.update(h),s.set(h,u)),c.isInstancedMesh&&(c.hasEventListener("dispose",l)===!1&&c.addEventListener("dispose",l),s.get(c)!==u&&(t.update(c.instanceMatrix,n.ARRAY_BUFFER),c.instanceColor!==null&&t.update(c.instanceColor,n.ARRAY_BUFFER),s.set(c,u))),c.isSkinnedMesh){const d=c.skeleton;s.get(d)!==u&&(d.update(),s.set(d,u))}return h}function o(){s=new WeakMap}function l(c){const u=c.target;u.removeEventListener("dispose",l),r.releaseStatesOfObject(u),t.remove(u.instanceMatrix),u.instanceColor!==null&&t.remove(u.instanceColor)}return{update:a,dispose:o}}const cM={[hm]:"LINEAR_TONE_MAPPING",[fm]:"REINHARD_TONE_MAPPING",[dm]:"CINEON_TONE_MAPPING",[pm]:"ACES_FILMIC_TONE_MAPPING",[gm]:"AGX_TONE_MAPPING",[_m]:"NEUTRAL_TONE_MAPPING",[mm]:"CUSTOM_TONE_MAPPING"};function uM(n,e,t,r,i){const s=new $t(e,t,{type:n,depthBuffer:r,stencilBuffer:i,depthTexture:r?new Wi(e,t):void 0}),a=new $t(e,t,{type:Yi,depthBuffer:!1,stencilBuffer:!1}),o=new Dt;o.setAttribute("position",new ui([-1,3,0,-1,-1,0,3,-1,0],3)),o.setAttribute("uv",new ui([0,2,0,0,2,0],2));const l=new iv({uniforms:{tDiffuse:{value:null}},vertexShader:`
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
			}`,depthTest:!1,depthWrite:!1}),c=new Wn(o,l),u=new Qh(-1,1,1,-1,0,1);let f=null,h=null,d=!1,m,g=null,p=[],_=!1;this.setSize=function(M,y){s.setSize(M,y),a.setSize(M,y);for(let v=0;v<p.length;v++){const S=p[v];S.setSize&&S.setSize(M,y)}},this.setEffects=function(M){p=M,_=p.length>0&&p[0].isRenderPass===!0;const y=s.width,v=s.height;for(let S=0;S<p.length;S++){const b=p[S];b.setSize&&b.setSize(y,v)}},this.begin=function(M,y){if(d||M.toneMapping===Pi&&p.length===0)return!1;if(g=y,y!==null){const v=y.width,S=y.height;(s.width!==v||s.height!==S)&&this.setSize(v,S)}return _===!1&&M.setRenderTarget(s),m=M.toneMapping,M.toneMapping=Pi,!0},this.hasRenderPass=function(){return _},this.end=function(M,y){M.toneMapping=m,d=!0;let v=s,S=a;for(let b=0;b<p.length;b++){const E=p[b];if(E.enabled!==!1&&(E.render(M,S,v,y),E.needsSwap!==!1)){const x=v;v=S,S=x}}if(f!==M.outputColorSpace||h!==M.toneMapping){f=M.outputColorSpace,h=M.toneMapping,l.defines={},ut.getTransfer(f)===xt&&(l.defines.SRGB_TRANSFER="");const b=cM[h];b&&(l.defines[b]=""),l.needsUpdate=!0}l.uniforms.tDiffuse.value=v.texture,M.setRenderTarget(g),M.render(c,u),g=null,d=!1},this.isCompositing=function(){return d},this.dispose=function(){s.depthTexture&&s.depthTexture.dispose(),s.dispose(),a.dispose(),o.dispose(),l.dispose()}}const Wm=new Zt,dh=new Wi(1,1),Xm=new Am,Ym=new D_,qm=new Im,Nd=[],Od=[],Bd=new Float32Array(16),kd=new Float32Array(9),zd=new Float32Array(4);function Ks(n,e,t){const r=n[0];if(r<=0||r>0)return n;const i=e*t;let s=Nd[i];if(s===void 0&&(s=new Float32Array(i),Nd[i]=s),e!==0){r.toArray(s,0);for(let a=1,o=0;a!==e;++a)o+=t,n[a].toArray(s,o)}return s}function Jt(n,e){if(n.length!==e.length)return!1;for(let t=0,r=n.length;t<r;t++)if(n[t]!==e[t])return!1;return!0}function Qt(n,e){for(let t=0,r=e.length;t<r;t++)n[t]=e[t]}function Pl(n,e){let t=Od[e];t===void 0&&(t=new Int32Array(e),Od[e]=t);for(let r=0;r!==e;++r)t[r]=n.allocateTextureUnit();return t}function hM(n,e){const t=this.cache;t[0]!==e&&(n.uniform1f(this.addr,e),t[0]=e)}function fM(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(n.uniform2f(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(Jt(t,e))return;n.uniform2fv(this.addr,e),Qt(t,e)}}function dM(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(n.uniform3f(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else if(e.r!==void 0)(t[0]!==e.r||t[1]!==e.g||t[2]!==e.b)&&(n.uniform3f(this.addr,e.r,e.g,e.b),t[0]=e.r,t[1]=e.g,t[2]=e.b);else{if(Jt(t,e))return;n.uniform3fv(this.addr,e),Qt(t,e)}}function pM(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(n.uniform4f(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(Jt(t,e))return;n.uniform4fv(this.addr,e),Qt(t,e)}}function mM(n,e){const t=this.cache,r=e.elements;if(r===void 0){if(Jt(t,e))return;n.uniformMatrix2fv(this.addr,!1,e),Qt(t,e)}else{if(Jt(t,r))return;zd.set(r),n.uniformMatrix2fv(this.addr,!1,zd),Qt(t,r)}}function gM(n,e){const t=this.cache,r=e.elements;if(r===void 0){if(Jt(t,e))return;n.uniformMatrix3fv(this.addr,!1,e),Qt(t,e)}else{if(Jt(t,r))return;kd.set(r),n.uniformMatrix3fv(this.addr,!1,kd),Qt(t,r)}}function _M(n,e){const t=this.cache,r=e.elements;if(r===void 0){if(Jt(t,e))return;n.uniformMatrix4fv(this.addr,!1,e),Qt(t,e)}else{if(Jt(t,r))return;Bd.set(r),n.uniformMatrix4fv(this.addr,!1,Bd),Qt(t,r)}}function vM(n,e){const t=this.cache;t[0]!==e&&(n.uniform1i(this.addr,e),t[0]=e)}function xM(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(n.uniform2i(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(Jt(t,e))return;n.uniform2iv(this.addr,e),Qt(t,e)}}function MM(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(n.uniform3i(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else{if(Jt(t,e))return;n.uniform3iv(this.addr,e),Qt(t,e)}}function SM(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(n.uniform4i(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(Jt(t,e))return;n.uniform4iv(this.addr,e),Qt(t,e)}}function bM(n,e){const t=this.cache;t[0]!==e&&(n.uniform1ui(this.addr,e),t[0]=e)}function yM(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(n.uniform2ui(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(Jt(t,e))return;n.uniform2uiv(this.addr,e),Qt(t,e)}}function TM(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(n.uniform3ui(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else{if(Jt(t,e))return;n.uniform3uiv(this.addr,e),Qt(t,e)}}function EM(n,e){const t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(n.uniform4ui(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(Jt(t,e))return;n.uniform4uiv(this.addr,e),Qt(t,e)}}function wM(n,e,t){const r=this.cache,i=t.allocateTextureUnit();r[0]!==i&&(n.uniform1i(this.addr,i),r[0]=i);let s;this.type===n.SAMPLER_2D_SHADOW?(dh.compareFunction=t.isReversedDepthBuffer()?Kh:jh,s=dh):s=Wm,t.setTexture2D(e||s,i)}function AM(n,e,t){const r=this.cache,i=t.allocateTextureUnit();r[0]!==i&&(n.uniform1i(this.addr,i),r[0]=i),t.setTexture3D(e||Ym,i)}function RM(n,e,t){const r=this.cache,i=t.allocateTextureUnit();r[0]!==i&&(n.uniform1i(this.addr,i),r[0]=i),t.setTextureCube(e||qm,i)}function CM(n,e,t){const r=this.cache,i=t.allocateTextureUnit();r[0]!==i&&(n.uniform1i(this.addr,i),r[0]=i),t.setTexture2DArray(e||Xm,i)}function PM(n){switch(n){case 5126:return hM;case 35664:return fM;case 35665:return dM;case 35666:return pM;case 35674:return mM;case 35675:return gM;case 35676:return _M;case 5124:case 35670:return vM;case 35667:case 35671:return xM;case 35668:case 35672:return MM;case 35669:case 35673:return SM;case 5125:return bM;case 36294:return yM;case 36295:return TM;case 36296:return EM;case 35678:case 36198:case 36298:case 36306:case 35682:return wM;case 35679:case 36299:case 36307:return AM;case 35680:case 36300:case 36308:case 36293:return RM;case 36289:case 36303:case 36311:case 36292:return CM}}function DM(n,e){n.uniform1fv(this.addr,e)}function UM(n,e){const t=Ks(e,this.size,2);n.uniform2fv(this.addr,t)}function LM(n,e){const t=Ks(e,this.size,3);n.uniform3fv(this.addr,t)}function IM(n,e){const t=Ks(e,this.size,4);n.uniform4fv(this.addr,t)}function FM(n,e){const t=Ks(e,this.size,4);n.uniformMatrix2fv(this.addr,!1,t)}function NM(n,e){const t=Ks(e,this.size,9);n.uniformMatrix3fv(this.addr,!1,t)}function OM(n,e){const t=Ks(e,this.size,16);n.uniformMatrix4fv(this.addr,!1,t)}function BM(n,e){n.uniform1iv(this.addr,e)}function kM(n,e){n.uniform2iv(this.addr,e)}function zM(n,e){n.uniform3iv(this.addr,e)}function GM(n,e){n.uniform4iv(this.addr,e)}function HM(n,e){n.uniform1uiv(this.addr,e)}function VM(n,e){n.uniform2uiv(this.addr,e)}function WM(n,e){n.uniform3uiv(this.addr,e)}function XM(n,e){n.uniform4uiv(this.addr,e)}function YM(n,e,t){const r=this.cache,i=e.length,s=Pl(t,i);Jt(r,s)||(n.uniform1iv(this.addr,s),Qt(r,s));let a;this.type===n.SAMPLER_2D_SHADOW?a=dh:a=Wm;for(let o=0;o!==i;++o)t.setTexture2D(e[o]||a,s[o])}function qM(n,e,t){const r=this.cache,i=e.length,s=Pl(t,i);Jt(r,s)||(n.uniform1iv(this.addr,s),Qt(r,s));for(let a=0;a!==i;++a)t.setTexture3D(e[a]||Ym,s[a])}function jM(n,e,t){const r=this.cache,i=e.length,s=Pl(t,i);Jt(r,s)||(n.uniform1iv(this.addr,s),Qt(r,s));for(let a=0;a!==i;++a)t.setTextureCube(e[a]||qm,s[a])}function KM(n,e,t){const r=this.cache,i=e.length,s=Pl(t,i);Jt(r,s)||(n.uniform1iv(this.addr,s),Qt(r,s));for(let a=0;a!==i;++a)t.setTexture2DArray(e[a]||Xm,s[a])}function ZM(n){switch(n){case 5126:return DM;case 35664:return UM;case 35665:return LM;case 35666:return IM;case 35674:return FM;case 35675:return NM;case 35676:return OM;case 5124:case 35670:return BM;case 35667:case 35671:return kM;case 35668:case 35672:return zM;case 35669:case 35673:return GM;case 5125:return HM;case 36294:return VM;case 36295:return WM;case 36296:return XM;case 35678:case 36198:case 36298:case 36306:case 35682:return YM;case 35679:case 36299:case 36307:return qM;case 35680:case 36300:case 36308:case 36293:return jM;case 36289:case 36303:case 36311:case 36292:return KM}}class $M{constructor(e,t,r){this.id=e,this.addr=r,this.cache=[],this.type=t.type,this.setValue=PM(t.type)}}class JM{constructor(e,t,r){this.id=e,this.addr=r,this.cache=[],this.type=t.type,this.size=t.size,this.setValue=ZM(t.type)}}class QM{constructor(e){this.id=e,this.seq=[],this.map={}}setValue(e,t,r){const i=this.seq;for(let s=0,a=i.length;s!==a;++s){const o=i[s];o.setValue(e,t[o.id],r)}}}const Ic=/(\w+)(\])?(\[|\.)?/g;function Gd(n,e){n.seq.push(e),n.map[e.id]=e}function eS(n,e,t){const r=n.name,i=r.length;for(Ic.lastIndex=0;;){const s=Ic.exec(r),a=Ic.lastIndex;let o=s[1];const l=s[2]==="]",c=s[3];if(l&&(o=o|0),c===void 0||c==="["&&a+2===i){Gd(t,c===void 0?new $M(o,n,e):new JM(o,n,e));break}else{let f=t.map[o];f===void 0&&(f=new QM(o),Gd(t,f)),t=f}}}class Zo{constructor(e,t){this.seq=[],this.map={};const r=e.getProgramParameter(t,e.ACTIVE_UNIFORMS);for(let a=0;a<r;++a){const o=e.getActiveUniform(t,a),l=e.getUniformLocation(t,o.name);eS(o,l,this)}const i=[],s=[];for(const a of this.seq)a.type===e.SAMPLER_2D_SHADOW||a.type===e.SAMPLER_CUBE_SHADOW||a.type===e.SAMPLER_2D_ARRAY_SHADOW?i.push(a):s.push(a);i.length>0&&(this.seq=i.concat(s))}setValue(e,t,r,i){const s=this.map[t];s!==void 0&&s.setValue(e,r,i)}setOptional(e,t,r){const i=t[r];i!==void 0&&this.setValue(e,r,i)}static upload(e,t,r,i){for(let s=0,a=t.length;s!==a;++s){const o=t[s],l=r[o.id];l.needsUpdate!==!1&&o.setValue(e,l.value,i)}}static seqWithValue(e,t){const r=[];for(let i=0,s=e.length;i!==s;++i){const a=e[i];a.id in t&&r.push(a)}return r}}function Hd(n,e,t){const r=n.createShader(e);return n.shaderSource(r,t),n.compileShader(r),r}const tS=37297;let nS=0;function iS(n,e){const t=n.split(`
`),r=[],i=Math.max(e-6,0),s=Math.min(e+6,t.length);for(let a=i;a<s;a++){const o=a+1;r.push(`${o===e?">":" "} ${o}: ${t[a]}`)}return r.join(`
`)}const Vd=new nt;function rS(n){ut._getMatrix(Vd,ut.workingColorSpace,n);const e=`mat3( ${Vd.elements.map(t=>t.toFixed(4))} )`;switch(ut.getTransfer(n)){case al:return[e,"LinearTransferOETF"];case xt:return[e,"sRGBTransferOETF"];default:return $e("WebGLProgram: Unsupported color space: ",n),[e,"LinearTransferOETF"]}}function Wd(n,e,t){const r=n.getShaderParameter(e,n.COMPILE_STATUS),s=(n.getShaderInfoLog(e)||"").trim();if(r&&s==="")return"";const a=/ERROR: 0:(\d+)/.exec(s);if(a){const o=parseInt(a[1]);return t.toUpperCase()+`

`+s+`

`+iS(n.getShaderSource(e),o)}else return s}function sS(n,e){const t=rS(e);return[`vec4 ${n}( vec4 value ) {`,`	return ${t[1]}( vec4( value.rgb * ${t[0]}, value.a ) );`,"}"].join(`
`)}const aS={[hm]:"Linear",[fm]:"Reinhard",[dm]:"Cineon",[pm]:"ACESFilmic",[gm]:"AgX",[_m]:"Neutral",[mm]:"Custom"};function oS(n,e){const t=aS[e];return t===void 0?($e("WebGLProgram: Unsupported toneMapping:",e),"vec3 "+n+"( vec3 color ) { return LinearToneMapping( color ); }"):"vec3 "+n+"( vec3 color ) { return "+t+"ToneMapping( color ); }"}const Io=new X;function lS(){ut.getLuminanceCoefficients(Io);const n=Io.x.toFixed(4),e=Io.y.toFixed(4),t=Io.z.toFixed(4);return["float luminance( const in vec3 rgb ) {",`	const vec3 weights = vec3( ${n}, ${e}, ${t} );`,"	return dot( weights, rgb );","}"].join(`
`)}function cS(n){return[n.extensionClipCullDistance?"#extension GL_ANGLE_clip_cull_distance : require":"",n.extensionMultiDraw?"#extension GL_ANGLE_multi_draw : require":""].filter(Ea).join(`
`)}function uS(n){const e=[];for(const t in n){const r=n[t];r!==!1&&e.push("#define "+t+" "+r)}return e.join(`
`)}function hS(n,e){const t={},r=n.getProgramParameter(e,n.ACTIVE_ATTRIBUTES);for(let i=0;i<r;i++){const s=n.getActiveAttrib(e,i),a=s.name;let o=1;s.type===n.FLOAT_MAT2&&(o=2),s.type===n.FLOAT_MAT3&&(o=3),s.type===n.FLOAT_MAT4&&(o=4),t[a]={type:s.type,location:n.getAttribLocation(e,a),locationSize:o}}return t}function Ea(n){return n!==""}function Xd(n,e){const t=e.numSpotLightShadows+e.numSpotLightMaps-e.numSpotLightShadowsWithMaps;return n.replace(/NUM_DIR_LIGHTS/g,e.numDirLights).replace(/NUM_SPOT_LIGHTS/g,e.numSpotLights).replace(/NUM_SPOT_LIGHT_MAPS/g,e.numSpotLightMaps).replace(/NUM_SPOT_LIGHT_COORDS/g,t).replace(/NUM_RECT_AREA_LIGHTS/g,e.numRectAreaLights).replace(/NUM_POINT_LIGHTS/g,e.numPointLights).replace(/NUM_HEMI_LIGHTS/g,e.numHemiLights).replace(/NUM_DIR_LIGHT_SHADOWS/g,e.numDirLightShadows).replace(/NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS/g,e.numSpotLightShadowsWithMaps).replace(/NUM_SPOT_LIGHT_SHADOWS/g,e.numSpotLightShadows).replace(/NUM_POINT_LIGHT_SHADOWS/g,e.numPointLightShadows)}function Yd(n,e){return n.replace(/NUM_CLIPPING_PLANES/g,e.numClippingPlanes).replace(/UNION_CLIPPING_PLANES/g,e.numClippingPlanes-e.numClipIntersection)}const fS=/^[ \t]*#include +<([\w\d./]+)>/gm;function ph(n){return n.replace(fS,pS)}const dS=new Map;function pS(n,e){let t=it[e];if(t===void 0){const r=dS.get(e);if(r!==void 0)t=it[r],$e('WebGLRenderer: Shader chunk "%s" has been deprecated. Use "%s" instead.',e,r);else throw new Error("Can not resolve #include <"+e+">")}return ph(t)}const mS=/#pragma unroll_loop_start\s+for\s*\(\s*int\s+i\s*=\s*(\d+)\s*;\s*i\s*<\s*(\d+)\s*;\s*i\s*\+\+\s*\)\s*{([\s\S]+?)}\s+#pragma unroll_loop_end/g;function qd(n){return n.replace(mS,gS)}function gS(n,e,t,r){let i="";for(let s=parseInt(e);s<parseInt(t);s++)i+=r.replace(/\[\s*i\s*\]/g,"[ "+s+" ]").replace(/UNROLLED_LOOP_INDEX/g,s);return i}function jd(n){let e=`precision ${n.precision} float;
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
#define LOW_PRECISION`),e}const _S={[Vo]:"SHADOWMAP_TYPE_PCF",[ya]:"SHADOWMAP_TYPE_VSM"};function vS(n){return _S[n.shadowMapType]||"SHADOWMAP_TYPE_BASIC"}const xS={[jr]:"ENVMAP_TYPE_CUBE",[Os]:"ENVMAP_TYPE_CUBE",[Al]:"ENVMAP_TYPE_CUBE_UV"};function MS(n){return n.envMap===!1?"ENVMAP_TYPE_CUBE":xS[n.envMapMode]||"ENVMAP_TYPE_CUBE"}const SS={[Os]:"ENVMAP_MODE_REFRACTION"};function bS(n){return n.envMap===!1?"ENVMAP_MODE_REFLECTION":SS[n.envMapMode]||"ENVMAP_MODE_REFLECTION"}const yS={[um]:"ENVMAP_BLENDING_MULTIPLY",[c_]:"ENVMAP_BLENDING_MIX",[u_]:"ENVMAP_BLENDING_ADD"};function TS(n){return n.envMap===!1?"ENVMAP_BLENDING_NONE":yS[n.combine]||"ENVMAP_BLENDING_NONE"}function ES(n){const e=n.envMapCubeUVHeight;if(e===null)return null;const t=Math.log2(e)-2,r=1/e;return{texelWidth:1/(3*Math.max(Math.pow(2,t),112)),texelHeight:r,maxMip:t}}function wS(n,e,t,r){const i=n.getContext(),s=t.defines;let a=t.vertexShader,o=t.fragmentShader;const l=vS(t),c=MS(t),u=bS(t),f=TS(t),h=ES(t),d=cS(t),m=uS(s),g=i.createProgram();let p,_,M=t.glslVersion?"#version "+t.glslVersion+`
`:"";t.isRawShaderMaterial?(p=["#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,m].filter(Ea).join(`
`),p.length>0&&(p+=`
`),_=["#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,m].filter(Ea).join(`
`),_.length>0&&(_+=`
`)):(p=[jd(t),"#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,m,t.extensionClipCullDistance?"#define USE_CLIP_DISTANCE":"",t.batching?"#define USE_BATCHING":"",t.batchingColor?"#define USE_BATCHING_COLOR":"",t.instancing?"#define USE_INSTANCING":"",t.instancingColor?"#define USE_INSTANCING_COLOR":"",t.instancingMorph?"#define USE_INSTANCING_MORPH":"",t.useFog&&t.fog?"#define USE_FOG":"",t.useFog&&t.fogExp2?"#define FOG_EXP2":"",t.map?"#define USE_MAP":"",t.envMap?"#define USE_ENVMAP":"",t.envMap?"#define "+u:"",t.lightMap?"#define USE_LIGHTMAP":"",t.aoMap?"#define USE_AOMAP":"",t.bumpMap?"#define USE_BUMPMAP":"",t.normalMap?"#define USE_NORMALMAP":"",t.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",t.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",t.displacementMap?"#define USE_DISPLACEMENTMAP":"",t.emissiveMap?"#define USE_EMISSIVEMAP":"",t.anisotropy?"#define USE_ANISOTROPY":"",t.anisotropyMap?"#define USE_ANISOTROPYMAP":"",t.clearcoatMap?"#define USE_CLEARCOATMAP":"",t.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",t.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",t.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",t.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",t.specularMap?"#define USE_SPECULARMAP":"",t.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",t.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",t.roughnessMap?"#define USE_ROUGHNESSMAP":"",t.metalnessMap?"#define USE_METALNESSMAP":"",t.alphaMap?"#define USE_ALPHAMAP":"",t.alphaHash?"#define USE_ALPHAHASH":"",t.transmission?"#define USE_TRANSMISSION":"",t.transmissionMap?"#define USE_TRANSMISSIONMAP":"",t.thicknessMap?"#define USE_THICKNESSMAP":"",t.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",t.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",t.mapUv?"#define MAP_UV "+t.mapUv:"",t.alphaMapUv?"#define ALPHAMAP_UV "+t.alphaMapUv:"",t.lightMapUv?"#define LIGHTMAP_UV "+t.lightMapUv:"",t.aoMapUv?"#define AOMAP_UV "+t.aoMapUv:"",t.emissiveMapUv?"#define EMISSIVEMAP_UV "+t.emissiveMapUv:"",t.bumpMapUv?"#define BUMPMAP_UV "+t.bumpMapUv:"",t.normalMapUv?"#define NORMALMAP_UV "+t.normalMapUv:"",t.displacementMapUv?"#define DISPLACEMENTMAP_UV "+t.displacementMapUv:"",t.metalnessMapUv?"#define METALNESSMAP_UV "+t.metalnessMapUv:"",t.roughnessMapUv?"#define ROUGHNESSMAP_UV "+t.roughnessMapUv:"",t.anisotropyMapUv?"#define ANISOTROPYMAP_UV "+t.anisotropyMapUv:"",t.clearcoatMapUv?"#define CLEARCOATMAP_UV "+t.clearcoatMapUv:"",t.clearcoatNormalMapUv?"#define CLEARCOAT_NORMALMAP_UV "+t.clearcoatNormalMapUv:"",t.clearcoatRoughnessMapUv?"#define CLEARCOAT_ROUGHNESSMAP_UV "+t.clearcoatRoughnessMapUv:"",t.iridescenceMapUv?"#define IRIDESCENCEMAP_UV "+t.iridescenceMapUv:"",t.iridescenceThicknessMapUv?"#define IRIDESCENCE_THICKNESSMAP_UV "+t.iridescenceThicknessMapUv:"",t.sheenColorMapUv?"#define SHEEN_COLORMAP_UV "+t.sheenColorMapUv:"",t.sheenRoughnessMapUv?"#define SHEEN_ROUGHNESSMAP_UV "+t.sheenRoughnessMapUv:"",t.specularMapUv?"#define SPECULARMAP_UV "+t.specularMapUv:"",t.specularColorMapUv?"#define SPECULAR_COLORMAP_UV "+t.specularColorMapUv:"",t.specularIntensityMapUv?"#define SPECULAR_INTENSITYMAP_UV "+t.specularIntensityMapUv:"",t.transmissionMapUv?"#define TRANSMISSIONMAP_UV "+t.transmissionMapUv:"",t.thicknessMapUv?"#define THICKNESSMAP_UV "+t.thicknessMapUv:"",t.vertexTangents&&t.flatShading===!1?"#define USE_TANGENT":"",t.vertexNormals?"#define HAS_NORMAL":"",t.vertexColors?"#define USE_COLOR":"",t.vertexAlphas?"#define USE_COLOR_ALPHA":"",t.vertexUv1s?"#define USE_UV1":"",t.vertexUv2s?"#define USE_UV2":"",t.vertexUv3s?"#define USE_UV3":"",t.pointsUvs?"#define USE_POINTS_UV":"",t.flatShading?"#define FLAT_SHADED":"",t.skinning?"#define USE_SKINNING":"",t.morphTargets?"#define USE_MORPHTARGETS":"",t.morphNormals&&t.flatShading===!1?"#define USE_MORPHNORMALS":"",t.morphColors?"#define USE_MORPHCOLORS":"",t.morphTargetsCount>0?"#define MORPHTARGETS_TEXTURE_STRIDE "+t.morphTextureStride:"",t.morphTargetsCount>0?"#define MORPHTARGETS_COUNT "+t.morphTargetsCount:"",t.doubleSided?"#define DOUBLE_SIDED":"",t.flipSided?"#define FLIP_SIDED":"",t.shadowMapEnabled?"#define USE_SHADOWMAP":"",t.shadowMapEnabled?"#define "+l:"",t.sizeAttenuation?"#define USE_SIZEATTENUATION":"",t.numLightProbes>0?"#define USE_LIGHT_PROBES":"",t.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",t.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 modelMatrix;","uniform mat4 modelViewMatrix;","uniform mat4 projectionMatrix;","uniform mat4 viewMatrix;","uniform mat3 normalMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;","#ifdef USE_INSTANCING","	attribute mat4 instanceMatrix;","#endif","#ifdef USE_INSTANCING_COLOR","	attribute vec3 instanceColor;","#endif","#ifdef USE_INSTANCING_MORPH","	uniform sampler2D morphTexture;","#endif","attribute vec3 position;","attribute vec3 normal;","attribute vec2 uv;","#ifdef USE_UV1","	attribute vec2 uv1;","#endif","#ifdef USE_UV2","	attribute vec2 uv2;","#endif","#ifdef USE_UV3","	attribute vec2 uv3;","#endif","#ifdef USE_TANGENT","	attribute vec4 tangent;","#endif","#if defined( USE_COLOR_ALPHA )","	attribute vec4 color;","#elif defined( USE_COLOR )","	attribute vec3 color;","#endif","#ifdef USE_SKINNING","	attribute vec4 skinIndex;","	attribute vec4 skinWeight;","#endif",`
`].filter(Ea).join(`
`),_=[jd(t),"#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,m,t.useFog&&t.fog?"#define USE_FOG":"",t.useFog&&t.fogExp2?"#define FOG_EXP2":"",t.alphaToCoverage?"#define ALPHA_TO_COVERAGE":"",t.map?"#define USE_MAP":"",t.matcap?"#define USE_MATCAP":"",t.envMap?"#define USE_ENVMAP":"",t.envMap?"#define "+c:"",t.envMap?"#define "+u:"",t.envMap?"#define "+f:"",h?"#define CUBEUV_TEXEL_WIDTH "+h.texelWidth:"",h?"#define CUBEUV_TEXEL_HEIGHT "+h.texelHeight:"",h?"#define CUBEUV_MAX_MIP "+h.maxMip+".0":"",t.lightMap?"#define USE_LIGHTMAP":"",t.aoMap?"#define USE_AOMAP":"",t.bumpMap?"#define USE_BUMPMAP":"",t.normalMap?"#define USE_NORMALMAP":"",t.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",t.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",t.packedNormalMap?"#define USE_PACKED_NORMALMAP":"",t.emissiveMap?"#define USE_EMISSIVEMAP":"",t.anisotropy?"#define USE_ANISOTROPY":"",t.anisotropyMap?"#define USE_ANISOTROPYMAP":"",t.clearcoat?"#define USE_CLEARCOAT":"",t.clearcoatMap?"#define USE_CLEARCOATMAP":"",t.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",t.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",t.dispersion?"#define USE_DISPERSION":"",t.iridescence?"#define USE_IRIDESCENCE":"",t.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",t.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",t.specularMap?"#define USE_SPECULARMAP":"",t.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",t.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",t.roughnessMap?"#define USE_ROUGHNESSMAP":"",t.metalnessMap?"#define USE_METALNESSMAP":"",t.alphaMap?"#define USE_ALPHAMAP":"",t.alphaTest?"#define USE_ALPHATEST":"",t.alphaHash?"#define USE_ALPHAHASH":"",t.sheen?"#define USE_SHEEN":"",t.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",t.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",t.transmission?"#define USE_TRANSMISSION":"",t.transmissionMap?"#define USE_TRANSMISSIONMAP":"",t.thicknessMap?"#define USE_THICKNESSMAP":"",t.vertexTangents&&t.flatShading===!1?"#define USE_TANGENT":"",t.vertexColors||t.instancingColor?"#define USE_COLOR":"",t.vertexAlphas||t.batchingColor?"#define USE_COLOR_ALPHA":"",t.vertexUv1s?"#define USE_UV1":"",t.vertexUv2s?"#define USE_UV2":"",t.vertexUv3s?"#define USE_UV3":"",t.pointsUvs?"#define USE_POINTS_UV":"",t.gradientMap?"#define USE_GRADIENTMAP":"",t.flatShading?"#define FLAT_SHADED":"",t.doubleSided?"#define DOUBLE_SIDED":"",t.flipSided?"#define FLIP_SIDED":"",t.shadowMapEnabled?"#define USE_SHADOWMAP":"",t.shadowMapEnabled?"#define "+l:"",t.premultipliedAlpha?"#define PREMULTIPLIED_ALPHA":"",t.numLightProbes>0?"#define USE_LIGHT_PROBES":"",t.numLightProbeGrids>0?"#define USE_LIGHT_PROBES_GRID":"",t.decodeVideoTexture?"#define DECODE_VIDEO_TEXTURE":"",t.decodeVideoTextureEmissive?"#define DECODE_VIDEO_TEXTURE_EMISSIVE":"",t.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",t.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 viewMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;",t.toneMapping!==Pi?"#define TONE_MAPPING":"",t.toneMapping!==Pi?it.tonemapping_pars_fragment:"",t.toneMapping!==Pi?oS("toneMapping",t.toneMapping):"",t.dithering?"#define DITHERING":"",t.opaque?"#define OPAQUE":"",it.colorspace_pars_fragment,sS("linearToOutputTexel",t.outputColorSpace),lS(),t.useDepthPacking?"#define DEPTH_PACKING "+t.depthPacking:"",`
`].filter(Ea).join(`
`)),a=ph(a),a=Xd(a,t),a=Yd(a,t),o=ph(o),o=Xd(o,t),o=Yd(o,t),a=qd(a),o=qd(o),t.isRawShaderMaterial!==!0&&(M=`#version 300 es
`,p=[d,"#define attribute in","#define varying out","#define texture2D texture"].join(`
`)+`
`+p,_=["#define varying in",t.glslVersion===Qf?"":"layout(location = 0) out highp vec4 pc_fragColor;",t.glslVersion===Qf?"":"#define gl_FragColor pc_fragColor","#define gl_FragDepthEXT gl_FragDepth","#define texture2D texture","#define textureCube texture","#define texture2DProj textureProj","#define texture2DLodEXT textureLod","#define texture2DProjLodEXT textureProjLod","#define textureCubeLodEXT textureLod","#define texture2DGradEXT textureGrad","#define texture2DProjGradEXT textureProjGrad","#define textureCubeGradEXT textureGrad"].join(`
`)+`
`+_);const y=M+p+a,v=M+_+o,S=Hd(i,i.VERTEX_SHADER,y),b=Hd(i,i.FRAGMENT_SHADER,v);i.attachShader(g,S),i.attachShader(g,b),t.index0AttributeName!==void 0?i.bindAttribLocation(g,0,t.index0AttributeName):t.morphTargets===!0&&i.bindAttribLocation(g,0,"position"),i.linkProgram(g);function E(L){if(n.debug.checkShaderErrors){const A=i.getProgramInfoLog(g)||"",U=i.getShaderInfoLog(S)||"",P=i.getShaderInfoLog(b)||"",I=A.trim(),F=U.trim(),O=P.trim();let q=!0,z=!0;if(i.getProgramParameter(g,i.LINK_STATUS)===!1)if(q=!1,typeof n.debug.onShaderError=="function")n.debug.onShaderError(i,g,S,b);else{const k=Wd(i,S,"vertex"),N=Wd(i,b,"fragment");ft("THREE.WebGLProgram: Shader Error "+i.getError()+" - VALIDATE_STATUS "+i.getProgramParameter(g,i.VALIDATE_STATUS)+`

Material Name: `+L.name+`
Material Type: `+L.type+`

Program Info Log: `+I+`
`+k+`
`+N)}else I!==""?$e("WebGLProgram: Program Info Log:",I):(F===""||O==="")&&(z=!1);z&&(L.diagnostics={runnable:q,programLog:I,vertexShader:{log:F,prefix:p},fragmentShader:{log:O,prefix:_}})}i.deleteShader(S),i.deleteShader(b),x=new Zo(i,g),w=hS(i,g)}let x;this.getUniforms=function(){return x===void 0&&E(this),x};let w;this.getAttributes=function(){return w===void 0&&E(this),w};let R=t.rendererExtensionParallelShaderCompile===!1;return this.isReady=function(){return R===!1&&(R=i.getProgramParameter(g,tS)),R},this.destroy=function(){r.releaseStatesOfProgram(this),i.deleteProgram(g),this.program=void 0},this.type=t.shaderType,this.name=t.shaderName,this.id=nS++,this.cacheKey=e,this.usedTimes=1,this.program=g,this.vertexShader=S,this.fragmentShader=b,this}let AS=0;class RS{constructor(){this.shaderCache=new Map,this.materialCache=new Map}update(e){const t=e.vertexShader,r=e.fragmentShader,i=this._getShaderStage(t),s=this._getShaderStage(r),a=this._getShaderCacheForMaterial(e);return a.has(i)===!1&&(a.add(i),i.usedTimes++),a.has(s)===!1&&(a.add(s),s.usedTimes++),this}remove(e){const t=this.materialCache.get(e);for(const r of t)r.usedTimes--,r.usedTimes===0&&this.shaderCache.delete(r.code);return this.materialCache.delete(e),this}getVertexShaderID(e){return this._getShaderStage(e.vertexShader).id}getFragmentShaderID(e){return this._getShaderStage(e.fragmentShader).id}dispose(){this.shaderCache.clear(),this.materialCache.clear()}_getShaderCacheForMaterial(e){const t=this.materialCache;let r=t.get(e);return r===void 0&&(r=new Set,t.set(e,r)),r}_getShaderStage(e){const t=this.shaderCache;let r=t.get(e);return r===void 0&&(r=new CS(e),t.set(e,r)),r}}class CS{constructor(e){this.id=AS++,this.code=e,this.usedTimes=0}}function PS(n){return n===Kr||n===rl||n===sl}function DS(n,e,t,r,i,s){const a=new Rm,o=new RS,l=new Set,c=[],u=new Map,f=r.logarithmicDepthBuffer;let h=r.precision;const d={MeshDepthMaterial:"depth",MeshDistanceMaterial:"distance",MeshNormalMaterial:"normal",MeshBasicMaterial:"basic",MeshLambertMaterial:"lambert",MeshPhongMaterial:"phong",MeshToonMaterial:"toon",MeshStandardMaterial:"physical",MeshPhysicalMaterial:"physical",MeshMatcapMaterial:"matcap",LineBasicMaterial:"basic",LineDashedMaterial:"dashed",PointsMaterial:"points",ShadowMaterial:"shadow",SpriteMaterial:"sprite"};function m(x){return l.add(x),x===0?"uv":`uv${x}`}function g(x,w,R,L,A,U){const P=L.fog,I=A.geometry,F=x.isMeshStandardMaterial||x.isMeshLambertMaterial||x.isMeshPhongMaterial?L.environment:null,O=x.isMeshStandardMaterial||x.isMeshLambertMaterial&&!x.envMap||x.isMeshPhongMaterial&&!x.envMap,q=e.get(x.envMap||F,O),z=q&&q.mapping===Al?q.image.height:null,k=d[x.type];x.precision!==null&&(h=r.getMaxPrecision(x.precision),h!==x.precision&&$e("WebGLProgram.getParameters:",x.precision,"not supported, using",h,"instead."));const N=I.morphAttributes.position||I.morphAttributes.normal||I.morphAttributes.color,G=N!==void 0?N.length:0;let K=0;I.morphAttributes.position!==void 0&&(K=1),I.morphAttributes.normal!==void 0&&(K=2),I.morphAttributes.color!==void 0&&(K=3);let J,j,V,Y;if(k){const Ke=bi[k];J=Ke.vertexShader,j=Ke.fragmentShader}else J=x.vertexShader,j=x.fragmentShader,o.update(x),V=o.getVertexShaderID(x),Y=o.getFragmentShaderID(x);const Z=n.getRenderTarget(),fe=n.state.buffers.depth.getReversed(),_e=A.isInstancedMesh===!0,le=A.isBatchedMesh===!0,de=!!x.map,Fe=!!x.matcap,Ne=!!q,Ae=!!x.aoMap,be=!!x.lightMap,ze=!!x.bumpMap,ge=!!x.normalMap,ke=!!x.displacementMap,B=!!x.emissiveMap,ue=!!x.metalnessMap,De=!!x.roughnessMap,ye=x.anisotropy>0,ce=x.clearcoat>0,Te=x.dispersion>0,D=x.iridescence>0,T=x.sheen>0,H=x.transmission>0,Q=ye&&!!x.anisotropyMap,oe=ce&&!!x.clearcoatMap,me=ce&&!!x.clearcoatNormalMap,Me=ce&&!!x.clearcoatRoughnessMap,ee=D&&!!x.iridescenceMap,re=D&&!!x.iridescenceThicknessMap,he=T&&!!x.sheenColorMap,Re=T&&!!x.sheenRoughnessMap,ve=!!x.specularMap,Se=!!x.specularColorMap,Ge=!!x.specularIntensityMap,Ce=H&&!!x.transmissionMap,Ye=H&&!!x.thicknessMap,W=!!x.gradientMap,pe=!!x.alphaMap,ie=x.alphaTest>0,we=!!x.alphaHash,xe=!!x.extensions;let ae=Pi;x.toneMapped&&(Z===null||Z.isXRRenderTarget===!0)&&(ae=n.toneMapping);const Pe={shaderID:k,shaderType:x.type,shaderName:x.name,vertexShader:J,fragmentShader:j,defines:x.defines,customVertexShaderID:V,customFragmentShaderID:Y,isRawShaderMaterial:x.isRawShaderMaterial===!0,glslVersion:x.glslVersion,precision:h,batching:le,batchingColor:le&&A._colorsTexture!==null,instancing:_e,instancingColor:_e&&A.instanceColor!==null,instancingMorph:_e&&A.morphTexture!==null,outputColorSpace:Z===null?n.outputColorSpace:Z.isXRRenderTarget===!0?Z.texture.colorSpace:ut.workingColorSpace,alphaToCoverage:!!x.alphaToCoverage,map:de,matcap:Fe,envMap:Ne,envMapMode:Ne&&q.mapping,envMapCubeUVHeight:z,aoMap:Ae,lightMap:be,bumpMap:ze,normalMap:ge,displacementMap:ke,emissiveMap:B,normalMapObjectSpace:ge&&x.normalMapType===d_,normalMapTangentSpace:ge&&x.normalMapType===$f,packedNormalMap:ge&&x.normalMapType===$f&&PS(x.normalMap.format),metalnessMap:ue,roughnessMap:De,anisotropy:ye,anisotropyMap:Q,clearcoat:ce,clearcoatMap:oe,clearcoatNormalMap:me,clearcoatRoughnessMap:Me,dispersion:Te,iridescence:D,iridescenceMap:ee,iridescenceThicknessMap:re,sheen:T,sheenColorMap:he,sheenRoughnessMap:Re,specularMap:ve,specularColorMap:Se,specularIntensityMap:Ge,transmission:H,transmissionMap:Ce,thicknessMap:Ye,gradientMap:W,opaque:x.transparent===!1&&x.blending===zr&&x.alphaToCoverage===!1,alphaMap:pe,alphaTest:ie,alphaHash:we,combine:x.combine,mapUv:de&&m(x.map.channel),aoMapUv:Ae&&m(x.aoMap.channel),lightMapUv:be&&m(x.lightMap.channel),bumpMapUv:ze&&m(x.bumpMap.channel),normalMapUv:ge&&m(x.normalMap.channel),displacementMapUv:ke&&m(x.displacementMap.channel),emissiveMapUv:B&&m(x.emissiveMap.channel),metalnessMapUv:ue&&m(x.metalnessMap.channel),roughnessMapUv:De&&m(x.roughnessMap.channel),anisotropyMapUv:Q&&m(x.anisotropyMap.channel),clearcoatMapUv:oe&&m(x.clearcoatMap.channel),clearcoatNormalMapUv:me&&m(x.clearcoatNormalMap.channel),clearcoatRoughnessMapUv:Me&&m(x.clearcoatRoughnessMap.channel),iridescenceMapUv:ee&&m(x.iridescenceMap.channel),iridescenceThicknessMapUv:re&&m(x.iridescenceThicknessMap.channel),sheenColorMapUv:he&&m(x.sheenColorMap.channel),sheenRoughnessMapUv:Re&&m(x.sheenRoughnessMap.channel),specularMapUv:ve&&m(x.specularMap.channel),specularColorMapUv:Se&&m(x.specularColorMap.channel),specularIntensityMapUv:Ge&&m(x.specularIntensityMap.channel),transmissionMapUv:Ce&&m(x.transmissionMap.channel),thicknessMapUv:Ye&&m(x.thicknessMap.channel),alphaMapUv:pe&&m(x.alphaMap.channel),vertexTangents:!!I.attributes.tangent&&(ge||ye),vertexNormals:!!I.attributes.normal,vertexColors:x.vertexColors,vertexAlphas:x.vertexColors===!0&&!!I.attributes.color&&I.attributes.color.itemSize===4,pointsUvs:A.isPoints===!0&&!!I.attributes.uv&&(de||pe),fog:!!P,useFog:x.fog===!0,fogExp2:!!P&&P.isFogExp2,flatShading:x.wireframe===!1&&(x.flatShading===!0||I.attributes.normal===void 0&&ge===!1&&(x.isMeshLambertMaterial||x.isMeshPhongMaterial||x.isMeshStandardMaterial||x.isMeshPhysicalMaterial)),sizeAttenuation:x.sizeAttenuation===!0,logarithmicDepthBuffer:f,reversedDepthBuffer:fe,skinning:A.isSkinnedMesh===!0,morphTargets:I.morphAttributes.position!==void 0,morphNormals:I.morphAttributes.normal!==void 0,morphColors:I.morphAttributes.color!==void 0,morphTargetsCount:G,morphTextureStride:K,numDirLights:w.directional.length,numPointLights:w.point.length,numSpotLights:w.spot.length,numSpotLightMaps:w.spotLightMap.length,numRectAreaLights:w.rectArea.length,numHemiLights:w.hemi.length,numDirLightShadows:w.directionalShadowMap.length,numPointLightShadows:w.pointShadowMap.length,numSpotLightShadows:w.spotShadowMap.length,numSpotLightShadowsWithMaps:w.numSpotLightShadowsWithMaps,numLightProbes:w.numLightProbes,numLightProbeGrids:U.length,numClippingPlanes:s.numPlanes,numClipIntersection:s.numIntersection,dithering:x.dithering,shadowMapEnabled:n.shadowMap.enabled&&R.length>0,shadowMapType:n.shadowMap.type,toneMapping:ae,decodeVideoTexture:de&&x.map.isVideoTexture===!0&&ut.getTransfer(x.map.colorSpace)===xt,decodeVideoTextureEmissive:B&&x.emissiveMap.isVideoTexture===!0&&ut.getTransfer(x.emissiveMap.colorSpace)===xt,premultipliedAlpha:x.premultipliedAlpha,doubleSided:x.side===wn,flipSided:x.side===sn,useDepthPacking:x.depthPacking>=0,depthPacking:x.depthPacking||0,index0AttributeName:x.index0AttributeName,extensionClipCullDistance:xe&&x.extensions.clipCullDistance===!0&&t.has("WEBGL_clip_cull_distance"),extensionMultiDraw:(xe&&x.extensions.multiDraw===!0||le)&&t.has("WEBGL_multi_draw"),rendererExtensionParallelShaderCompile:t.has("KHR_parallel_shader_compile"),customProgramCacheKey:x.customProgramCacheKey()};return Pe.vertexUv1s=l.has(1),Pe.vertexUv2s=l.has(2),Pe.vertexUv3s=l.has(3),l.clear(),Pe}function p(x){const w=[];if(x.shaderID?w.push(x.shaderID):(w.push(x.customVertexShaderID),w.push(x.customFragmentShaderID)),x.defines!==void 0)for(const R in x.defines)w.push(R),w.push(x.defines[R]);return x.isRawShaderMaterial===!1&&(_(w,x),M(w,x),w.push(n.outputColorSpace)),w.push(x.customProgramCacheKey),w.join()}function _(x,w){x.push(w.precision),x.push(w.outputColorSpace),x.push(w.envMapMode),x.push(w.envMapCubeUVHeight),x.push(w.mapUv),x.push(w.alphaMapUv),x.push(w.lightMapUv),x.push(w.aoMapUv),x.push(w.bumpMapUv),x.push(w.normalMapUv),x.push(w.displacementMapUv),x.push(w.emissiveMapUv),x.push(w.metalnessMapUv),x.push(w.roughnessMapUv),x.push(w.anisotropyMapUv),x.push(w.clearcoatMapUv),x.push(w.clearcoatNormalMapUv),x.push(w.clearcoatRoughnessMapUv),x.push(w.iridescenceMapUv),x.push(w.iridescenceThicknessMapUv),x.push(w.sheenColorMapUv),x.push(w.sheenRoughnessMapUv),x.push(w.specularMapUv),x.push(w.specularColorMapUv),x.push(w.specularIntensityMapUv),x.push(w.transmissionMapUv),x.push(w.thicknessMapUv),x.push(w.combine),x.push(w.fogExp2),x.push(w.sizeAttenuation),x.push(w.morphTargetsCount),x.push(w.morphAttributeCount),x.push(w.numDirLights),x.push(w.numPointLights),x.push(w.numSpotLights),x.push(w.numSpotLightMaps),x.push(w.numHemiLights),x.push(w.numRectAreaLights),x.push(w.numDirLightShadows),x.push(w.numPointLightShadows),x.push(w.numSpotLightShadows),x.push(w.numSpotLightShadowsWithMaps),x.push(w.numLightProbes),x.push(w.shadowMapType),x.push(w.toneMapping),x.push(w.numClippingPlanes),x.push(w.numClipIntersection),x.push(w.depthPacking)}function M(x,w){a.disableAll(),w.instancing&&a.enable(0),w.instancingColor&&a.enable(1),w.instancingMorph&&a.enable(2),w.matcap&&a.enable(3),w.envMap&&a.enable(4),w.normalMapObjectSpace&&a.enable(5),w.normalMapTangentSpace&&a.enable(6),w.clearcoat&&a.enable(7),w.iridescence&&a.enable(8),w.alphaTest&&a.enable(9),w.vertexColors&&a.enable(10),w.vertexAlphas&&a.enable(11),w.vertexUv1s&&a.enable(12),w.vertexUv2s&&a.enable(13),w.vertexUv3s&&a.enable(14),w.vertexTangents&&a.enable(15),w.anisotropy&&a.enable(16),w.alphaHash&&a.enable(17),w.batching&&a.enable(18),w.dispersion&&a.enable(19),w.batchingColor&&a.enable(20),w.gradientMap&&a.enable(21),w.packedNormalMap&&a.enable(22),w.vertexNormals&&a.enable(23),x.push(a.mask),a.disableAll(),w.fog&&a.enable(0),w.useFog&&a.enable(1),w.flatShading&&a.enable(2),w.logarithmicDepthBuffer&&a.enable(3),w.reversedDepthBuffer&&a.enable(4),w.skinning&&a.enable(5),w.morphTargets&&a.enable(6),w.morphNormals&&a.enable(7),w.morphColors&&a.enable(8),w.premultipliedAlpha&&a.enable(9),w.shadowMapEnabled&&a.enable(10),w.doubleSided&&a.enable(11),w.flipSided&&a.enable(12),w.useDepthPacking&&a.enable(13),w.dithering&&a.enable(14),w.transmission&&a.enable(15),w.sheen&&a.enable(16),w.opaque&&a.enable(17),w.pointsUvs&&a.enable(18),w.decodeVideoTexture&&a.enable(19),w.decodeVideoTextureEmissive&&a.enable(20),w.alphaToCoverage&&a.enable(21),w.numLightProbeGrids>0&&a.enable(22),x.push(a.mask)}function y(x){const w=d[x.type];let R;if(w){const L=bi[w];R=Om.clone(L.uniforms)}else R=x.uniforms;return R}function v(x,w){let R=u.get(w);return R!==void 0?++R.usedTimes:(R=new wS(n,w,x,i),c.push(R),u.set(w,R)),R}function S(x){if(--x.usedTimes===0){const w=c.indexOf(x);c[w]=c[c.length-1],c.pop(),u.delete(x.cacheKey),x.destroy()}}function b(x){o.remove(x)}function E(){o.dispose()}return{getParameters:g,getProgramCacheKey:p,getUniforms:y,acquireProgram:v,releaseProgram:S,releaseShaderCache:b,programs:c,dispose:E}}function US(){let n=new WeakMap;function e(a){return n.has(a)}function t(a){let o=n.get(a);return o===void 0&&(o={},n.set(a,o)),o}function r(a){n.delete(a)}function i(a,o,l){n.get(a)[o]=l}function s(){n=new WeakMap}return{has:e,get:t,remove:r,update:i,dispose:s}}function LS(n,e){return n.groupOrder!==e.groupOrder?n.groupOrder-e.groupOrder:n.renderOrder!==e.renderOrder?n.renderOrder-e.renderOrder:n.material.id!==e.material.id?n.material.id-e.material.id:n.materialVariant!==e.materialVariant?n.materialVariant-e.materialVariant:n.z!==e.z?n.z-e.z:n.id-e.id}function Kd(n,e){return n.groupOrder!==e.groupOrder?n.groupOrder-e.groupOrder:n.renderOrder!==e.renderOrder?n.renderOrder-e.renderOrder:n.z!==e.z?e.z-n.z:n.id-e.id}function Zd(){const n=[];let e=0;const t=[],r=[],i=[];function s(){e=0,t.length=0,r.length=0,i.length=0}function a(h){let d=0;return h.isInstancedMesh&&(d+=2),h.isSkinnedMesh&&(d+=1),d}function o(h,d,m,g,p,_){let M=n[e];return M===void 0?(M={id:h.id,object:h,geometry:d,material:m,materialVariant:a(h),groupOrder:g,renderOrder:h.renderOrder,z:p,group:_},n[e]=M):(M.id=h.id,M.object=h,M.geometry=d,M.material=m,M.materialVariant=a(h),M.groupOrder=g,M.renderOrder=h.renderOrder,M.z=p,M.group=_),e++,M}function l(h,d,m,g,p,_){const M=o(h,d,m,g,p,_);m.transmission>0?r.push(M):m.transparent===!0?i.push(M):t.push(M)}function c(h,d,m,g,p,_){const M=o(h,d,m,g,p,_);m.transmission>0?r.unshift(M):m.transparent===!0?i.unshift(M):t.unshift(M)}function u(h,d){t.length>1&&t.sort(h||LS),r.length>1&&r.sort(d||Kd),i.length>1&&i.sort(d||Kd)}function f(){for(let h=e,d=n.length;h<d;h++){const m=n[h];if(m.id===null)break;m.id=null,m.object=null,m.geometry=null,m.material=null,m.group=null}}return{opaque:t,transmissive:r,transparent:i,init:s,push:l,unshift:c,finish:f,sort:u}}function IS(){let n=new WeakMap;function e(r,i){const s=n.get(r);let a;return s===void 0?(a=new Zd,n.set(r,[a])):i>=s.length?(a=new Zd,s.push(a)):a=s[i],a}function t(){n=new WeakMap}return{get:e,dispose:t}}function FS(){const n={};return{get:function(e){if(n[e.id]!==void 0)return n[e.id];let t;switch(e.type){case"DirectionalLight":t={direction:new X,color:new lt};break;case"SpotLight":t={position:new X,direction:new X,color:new lt,distance:0,coneCos:0,penumbraCos:0,decay:0};break;case"PointLight":t={position:new X,color:new lt,distance:0,decay:0};break;case"HemisphereLight":t={direction:new X,skyColor:new lt,groundColor:new lt};break;case"RectAreaLight":t={color:new lt,position:new X,halfWidth:new X,halfHeight:new X};break}return n[e.id]=t,t}}}function NS(){const n={};return{get:function(e){if(n[e.id]!==void 0)return n[e.id];let t;switch(e.type){case"DirectionalLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new We};break;case"SpotLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new We};break;case"PointLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new We,shadowCameraNear:1,shadowCameraFar:1e3};break}return n[e.id]=t,t}}}let OS=0;function BS(n,e){return(e.castShadow?2:0)-(n.castShadow?2:0)+(e.map?1:0)-(n.map?1:0)}function kS(n){const e=new FS,t=NS(),r={version:0,hash:{directionalLength:-1,pointLength:-1,spotLength:-1,rectAreaLength:-1,hemiLength:-1,numDirectionalShadows:-1,numPointShadows:-1,numSpotShadows:-1,numSpotMaps:-1,numLightProbes:-1},ambient:[0,0,0],probe:[],directional:[],directionalShadow:[],directionalShadowMap:[],directionalShadowMatrix:[],spot:[],spotLightMap:[],spotShadow:[],spotShadowMap:[],spotLightMatrix:[],rectArea:[],rectAreaLTC1:null,rectAreaLTC2:null,point:[],pointShadow:[],pointShadowMap:[],pointShadowMatrix:[],hemi:[],numSpotLightShadowsWithMaps:0,numLightProbes:0};for(let c=0;c<9;c++)r.probe.push(new X);const i=new X,s=new Ot,a=new Ot;function o(c){let u=0,f=0,h=0;for(let w=0;w<9;w++)r.probe[w].set(0,0,0);let d=0,m=0,g=0,p=0,_=0,M=0,y=0,v=0,S=0,b=0,E=0;c.sort(BS);for(let w=0,R=c.length;w<R;w++){const L=c[w],A=L.color,U=L.intensity,P=L.distance;let I=null;if(L.shadow&&L.shadow.map&&(L.shadow.map.texture.format===Kr?I=L.shadow.map.texture:I=L.shadow.map.depthTexture||L.shadow.map.texture),L.isAmbientLight)u+=A.r*U,f+=A.g*U,h+=A.b*U;else if(L.isLightProbe){for(let F=0;F<9;F++)r.probe[F].addScaledVector(L.sh.coefficients[F],U);E++}else if(L.isDirectionalLight){const F=e.get(L);if(F.color.copy(L.color).multiplyScalar(L.intensity),L.castShadow){const O=L.shadow,q=t.get(L);q.shadowIntensity=O.intensity,q.shadowBias=O.bias,q.shadowNormalBias=O.normalBias,q.shadowRadius=O.radius,q.shadowMapSize=O.mapSize,r.directionalShadow[d]=q,r.directionalShadowMap[d]=I,r.directionalShadowMatrix[d]=L.shadow.matrix,M++}r.directional[d]=F,d++}else if(L.isSpotLight){const F=e.get(L);F.position.setFromMatrixPosition(L.matrixWorld),F.color.copy(A).multiplyScalar(U),F.distance=P,F.coneCos=Math.cos(L.angle),F.penumbraCos=Math.cos(L.angle*(1-L.penumbra)),F.decay=L.decay,r.spot[g]=F;const O=L.shadow;if(L.map&&(r.spotLightMap[S]=L.map,S++,O.updateMatrices(L),L.castShadow&&b++),r.spotLightMatrix[g]=O.matrix,L.castShadow){const q=t.get(L);q.shadowIntensity=O.intensity,q.shadowBias=O.bias,q.shadowNormalBias=O.normalBias,q.shadowRadius=O.radius,q.shadowMapSize=O.mapSize,r.spotShadow[g]=q,r.spotShadowMap[g]=I,v++}g++}else if(L.isRectAreaLight){const F=e.get(L);F.color.copy(A).multiplyScalar(U),F.halfWidth.set(L.width*.5,0,0),F.halfHeight.set(0,L.height*.5,0),r.rectArea[p]=F,p++}else if(L.isPointLight){const F=e.get(L);if(F.color.copy(L.color).multiplyScalar(L.intensity),F.distance=L.distance,F.decay=L.decay,L.castShadow){const O=L.shadow,q=t.get(L);q.shadowIntensity=O.intensity,q.shadowBias=O.bias,q.shadowNormalBias=O.normalBias,q.shadowRadius=O.radius,q.shadowMapSize=O.mapSize,q.shadowCameraNear=O.camera.near,q.shadowCameraFar=O.camera.far,r.pointShadow[m]=q,r.pointShadowMap[m]=I,r.pointShadowMatrix[m]=L.shadow.matrix,y++}r.point[m]=F,m++}else if(L.isHemisphereLight){const F=e.get(L);F.skyColor.copy(L.color).multiplyScalar(U),F.groundColor.copy(L.groundColor).multiplyScalar(U),r.hemi[_]=F,_++}}p>0&&(n.has("OES_texture_float_linear")===!0?(r.rectAreaLTC1=Be.LTC_FLOAT_1,r.rectAreaLTC2=Be.LTC_FLOAT_2):(r.rectAreaLTC1=Be.LTC_HALF_1,r.rectAreaLTC2=Be.LTC_HALF_2)),r.ambient[0]=u,r.ambient[1]=f,r.ambient[2]=h;const x=r.hash;(x.directionalLength!==d||x.pointLength!==m||x.spotLength!==g||x.rectAreaLength!==p||x.hemiLength!==_||x.numDirectionalShadows!==M||x.numPointShadows!==y||x.numSpotShadows!==v||x.numSpotMaps!==S||x.numLightProbes!==E)&&(r.directional.length=d,r.spot.length=g,r.rectArea.length=p,r.point.length=m,r.hemi.length=_,r.directionalShadow.length=M,r.directionalShadowMap.length=M,r.pointShadow.length=y,r.pointShadowMap.length=y,r.spotShadow.length=v,r.spotShadowMap.length=v,r.directionalShadowMatrix.length=M,r.pointShadowMatrix.length=y,r.spotLightMatrix.length=v+S-b,r.spotLightMap.length=S,r.numSpotLightShadowsWithMaps=b,r.numLightProbes=E,x.directionalLength=d,x.pointLength=m,x.spotLength=g,x.rectAreaLength=p,x.hemiLength=_,x.numDirectionalShadows=M,x.numPointShadows=y,x.numSpotShadows=v,x.numSpotMaps=S,x.numLightProbes=E,r.version=OS++)}function l(c,u){let f=0,h=0,d=0,m=0,g=0;const p=u.matrixWorldInverse;for(let _=0,M=c.length;_<M;_++){const y=c[_];if(y.isDirectionalLight){const v=r.directional[f];v.direction.setFromMatrixPosition(y.matrixWorld),i.setFromMatrixPosition(y.target.matrixWorld),v.direction.sub(i),v.direction.transformDirection(p),f++}else if(y.isSpotLight){const v=r.spot[d];v.position.setFromMatrixPosition(y.matrixWorld),v.position.applyMatrix4(p),v.direction.setFromMatrixPosition(y.matrixWorld),i.setFromMatrixPosition(y.target.matrixWorld),v.direction.sub(i),v.direction.transformDirection(p),d++}else if(y.isRectAreaLight){const v=r.rectArea[m];v.position.setFromMatrixPosition(y.matrixWorld),v.position.applyMatrix4(p),a.identity(),s.copy(y.matrixWorld),s.premultiply(p),a.extractRotation(s),v.halfWidth.set(y.width*.5,0,0),v.halfHeight.set(0,y.height*.5,0),v.halfWidth.applyMatrix4(a),v.halfHeight.applyMatrix4(a),m++}else if(y.isPointLight){const v=r.point[h];v.position.setFromMatrixPosition(y.matrixWorld),v.position.applyMatrix4(p),h++}else if(y.isHemisphereLight){const v=r.hemi[g];v.direction.setFromMatrixPosition(y.matrixWorld),v.direction.transformDirection(p),g++}}}return{setup:o,setupView:l,state:r}}function $d(n){const e=new kS(n),t=[],r=[],i=[];function s(h){f.camera=h,t.length=0,r.length=0,i.length=0}function a(h){t.push(h)}function o(h){r.push(h)}function l(h){i.push(h)}function c(){e.setup(t)}function u(h){e.setupView(t,h)}const f={lightsArray:t,shadowsArray:r,lightProbeGridArray:i,camera:null,lights:e,transmissionRenderTarget:{},textureUnits:0};return{init:s,state:f,setupLights:c,setupLightsView:u,pushLight:a,pushShadow:o,pushLightProbeGrid:l}}function zS(n){let e=new WeakMap;function t(i,s=0){const a=e.get(i);let o;return a===void 0?(o=new $d(n),e.set(i,[o])):s>=a.length?(o=new $d(n),a.push(o)):o=a[s],o}function r(){e=new WeakMap}return{get:t,dispose:r}}const GS=`void main() {
	gl_Position = vec4( position, 1.0 );
}`,HS=`uniform sampler2D shadow_pass;
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
}`,VS=[new X(1,0,0),new X(-1,0,0),new X(0,1,0),new X(0,-1,0),new X(0,0,1),new X(0,0,-1)],WS=[new X(0,-1,0),new X(0,-1,0),new X(0,0,1),new X(0,0,-1),new X(0,-1,0),new X(0,-1,0)],Jd=new Ot,xa=new X,Fc=new X;function XS(n,e,t){let r=new Lm;const i=new We,s=new We,a=new Ct,o=new Bm,l=new km,c={},u=t.maxTextureSize,f={[Xi]:sn,[sn]:Xi,[wn]:wn},h=new an({defines:{VSM_SAMPLES:8},uniforms:{shadow_pass:{value:null},resolution:{value:new We},radius:{value:4}},vertexShader:GS,fragmentShader:HS}),d=h.clone();d.defines.HORIZONTAL_PASS=1;const m=new Dt;m.setAttribute("position",new kt(new Float32Array([-1,-1,.5,3,-1,.5,-1,3,.5]),3));const g=new Wn(m,h),p=this;this.enabled=!1,this.autoUpdate=!0,this.needsUpdate=!1,this.type=Vo;let _=this.type;this.render=function(b,E,x){if(p.enabled===!1||p.autoUpdate===!1&&p.needsUpdate===!1||b.length===0)return;this.type===Wg&&($e("WebGLShadowMap: PCFSoftShadowMap has been deprecated. Using PCFShadowMap instead."),this.type=Vo);const w=n.getRenderTarget(),R=n.getActiveCubeFace(),L=n.getActiveMipmapLevel(),A=n.state;A.setBlending(Sn),A.buffers.depth.getReversed()===!0?A.buffers.color.setClear(0,0,0,0):A.buffers.color.setClear(1,1,1,1),A.buffers.depth.setTest(!0),A.setScissorTest(!1);const U=_!==this.type;U&&E.traverse(function(P){P.material&&(Array.isArray(P.material)?P.material.forEach(I=>I.needsUpdate=!0):P.material.needsUpdate=!0)});for(let P=0,I=b.length;P<I;P++){const F=b[P],O=F.shadow;if(O===void 0){$e("WebGLShadowMap:",F,"has no shadow.");continue}if(O.autoUpdate===!1&&O.needsUpdate===!1)continue;i.copy(O.mapSize);const q=O.getFrameExtents();i.multiply(q),s.copy(O.mapSize),(i.x>u||i.y>u)&&(i.x>u&&(s.x=Math.floor(u/q.x),i.x=s.x*q.x,O.mapSize.x=s.x),i.y>u&&(s.y=Math.floor(u/q.y),i.y=s.y*q.y,O.mapSize.y=s.y));const z=n.state.buffers.depth.getReversed();if(O.camera._reversedDepth=z,O.map===null||U===!0){if(O.map!==null&&(O.map.depthTexture!==null&&(O.map.depthTexture.dispose(),O.map.depthTexture=null),O.map.dispose()),this.type===ya){if(F.isPointLight){$e("WebGLShadowMap: VSM shadow maps are not supported for PointLights. Use PCF or BasicShadowMap instead.");continue}O.map=new $t(i.x,i.y,{format:Kr,type:Yi,minFilter:zt,magFilter:zt,generateMipmaps:!1}),O.map.texture.name=F.name+".shadowMap",O.map.depthTexture=new Wi(i.x,i.y,li),O.map.depthTexture.name=F.name+".shadowMapDepth",O.map.depthTexture.format=qi,O.map.depthTexture.compareFunction=null,O.map.depthTexture.minFilter=cn,O.map.depthTexture.magFilter=cn}else F.isPointLight?(O.map=new Vm(i.x),O.map.depthTexture=new Q_(i.x,Di)):(O.map=new $t(i.x,i.y),O.map.depthTexture=new Wi(i.x,i.y,Di)),O.map.depthTexture.name=F.name+".shadowMap",O.map.depthTexture.format=qi,this.type===Vo?(O.map.depthTexture.compareFunction=z?Kh:jh,O.map.depthTexture.minFilter=zt,O.map.depthTexture.magFilter=zt):(O.map.depthTexture.compareFunction=null,O.map.depthTexture.minFilter=cn,O.map.depthTexture.magFilter=cn);O.camera.updateProjectionMatrix()}const k=O.map.isWebGLCubeRenderTarget?6:1;for(let N=0;N<k;N++){if(O.map.isWebGLCubeRenderTarget)n.setRenderTarget(O.map,N),n.clear();else{N===0&&(n.setRenderTarget(O.map),n.clear());const G=O.getViewport(N);a.set(s.x*G.x,s.y*G.y,s.x*G.z,s.y*G.w),A.viewport(a)}if(F.isPointLight){const G=O.camera,K=O.matrix,J=F.distance||G.far;J!==G.far&&(G.far=J,G.updateProjectionMatrix()),xa.setFromMatrixPosition(F.matrixWorld),G.position.copy(xa),Fc.copy(G.position),Fc.add(VS[N]),G.up.copy(WS[N]),G.lookAt(Fc),G.updateMatrixWorld(),K.makeTranslation(-xa.x,-xa.y,-xa.z),Jd.multiplyMatrices(G.projectionMatrix,G.matrixWorldInverse),O._frustum.setFromProjectionMatrix(Jd,G.coordinateSystem,G.reversedDepth)}else O.updateMatrices(F);r=O.getFrustum(),v(E,x,O.camera,F,this.type)}O.isPointLightShadow!==!0&&this.type===ya&&M(O,x),O.needsUpdate=!1}_=this.type,p.needsUpdate=!1,n.setRenderTarget(w,R,L)};function M(b,E){const x=e.update(g);h.defines.VSM_SAMPLES!==b.blurSamples&&(h.defines.VSM_SAMPLES=b.blurSamples,d.defines.VSM_SAMPLES=b.blurSamples,h.needsUpdate=!0,d.needsUpdate=!0),b.mapPass===null&&(b.mapPass=new $t(i.x,i.y,{format:Kr,type:Yi})),h.uniforms.shadow_pass.value=b.map.depthTexture,h.uniforms.resolution.value=b.mapSize,h.uniforms.radius.value=b.radius,n.setRenderTarget(b.mapPass),n.clear(),n.renderBufferDirect(E,null,x,h,g,null),d.uniforms.shadow_pass.value=b.mapPass.texture,d.uniforms.resolution.value=b.mapSize,d.uniforms.radius.value=b.radius,n.setRenderTarget(b.map),n.clear(),n.renderBufferDirect(E,null,x,d,g,null)}function y(b,E,x,w){let R=null;const L=x.isPointLight===!0?b.customDistanceMaterial:b.customDepthMaterial;if(L!==void 0)R=L;else if(R=x.isPointLight===!0?l:o,n.localClippingEnabled&&E.clipShadows===!0&&Array.isArray(E.clippingPlanes)&&E.clippingPlanes.length!==0||E.displacementMap&&E.displacementScale!==0||E.alphaMap&&E.alphaTest>0||E.map&&E.alphaTest>0||E.alphaToCoverage===!0){const A=R.uuid,U=E.uuid;let P=c[A];P===void 0&&(P={},c[A]=P);let I=P[U];I===void 0&&(I=R.clone(),P[U]=I,E.addEventListener("dispose",S)),R=I}if(R.visible=E.visible,R.wireframe=E.wireframe,w===ya?R.side=E.shadowSide!==null?E.shadowSide:E.side:R.side=E.shadowSide!==null?E.shadowSide:f[E.side],R.alphaMap=E.alphaMap,R.alphaTest=E.alphaToCoverage===!0?.5:E.alphaTest,R.map=E.map,R.clipShadows=E.clipShadows,R.clippingPlanes=E.clippingPlanes,R.clipIntersection=E.clipIntersection,R.displacementMap=E.displacementMap,R.displacementScale=E.displacementScale,R.displacementBias=E.displacementBias,R.wireframeLinewidth=E.wireframeLinewidth,R.linewidth=E.linewidth,x.isPointLight===!0&&R.isMeshDistanceMaterial===!0){const A=n.properties.get(R);A.light=x}return R}function v(b,E,x,w,R){if(b.visible===!1)return;if(b.layers.test(E.layers)&&(b.isMesh||b.isLine||b.isPoints)&&(b.castShadow||b.receiveShadow&&R===ya)&&(!b.frustumCulled||r.intersectsObject(b))){b.modelViewMatrix.multiplyMatrices(x.matrixWorldInverse,b.matrixWorld);const U=e.update(b),P=b.material;if(Array.isArray(P)){const I=U.groups;for(let F=0,O=I.length;F<O;F++){const q=I[F],z=P[q.materialIndex];if(z&&z.visible){const k=y(b,z,w,R);b.onBeforeShadow(n,b,E,x,U,k,q),n.renderBufferDirect(x,null,U,k,b,q),b.onAfterShadow(n,b,E,x,U,k,q)}}}else if(P.visible){const I=y(b,P,w,R);b.onBeforeShadow(n,b,E,x,U,I,null),n.renderBufferDirect(x,null,U,I,b,null),b.onAfterShadow(n,b,E,x,U,I,null)}}const A=b.children;for(let U=0,P=A.length;U<P;U++)v(A[U],E,x,w,R)}function S(b){b.target.removeEventListener("dispose",S);for(const x in c){const w=c[x],R=b.target.uuid;R in w&&(w[R].dispose(),delete w[R])}}}function YS(n,e){function t(){let W=!1;const pe=new Ct;let ie=null;const we=new Ct(0,0,0,0);return{setMask:function(xe){ie!==xe&&!W&&(n.colorMask(xe,xe,xe,xe),ie=xe)},setLocked:function(xe){W=xe},setClear:function(xe,ae,Pe,Ke,st){st===!0&&(xe*=Ke,ae*=Ke,Pe*=Ke),pe.set(xe,ae,Pe,Ke),we.equals(pe)===!1&&(n.clearColor(xe,ae,Pe,Ke),we.copy(pe))},reset:function(){W=!1,ie=null,we.set(-1,0,0,0)}}}function r(){let W=!1,pe=!1,ie=null,we=null,xe=null;return{setReversed:function(ae){if(pe!==ae){const Pe=e.get("EXT_clip_control");ae?Pe.clipControlEXT(Pe.LOWER_LEFT_EXT,Pe.ZERO_TO_ONE_EXT):Pe.clipControlEXT(Pe.LOWER_LEFT_EXT,Pe.NEGATIVE_ONE_TO_ONE_EXT),pe=ae;const Ke=xe;xe=null,this.setClear(Ke)}},getReversed:function(){return pe},setTest:function(ae){ae?Z(n.DEPTH_TEST):fe(n.DEPTH_TEST)},setMask:function(ae){ie!==ae&&!W&&(n.depthMask(ae),ie=ae)},setFunc:function(ae){if(pe&&(ae=y_[ae]),we!==ae){switch(ae){case yu:n.depthFunc(n.NEVER);break;case il:n.depthFunc(n.ALWAYS);break;case Tu:n.depthFunc(n.LESS);break;case Ns:n.depthFunc(n.LEQUAL);break;case Eu:n.depthFunc(n.EQUAL);break;case wu:n.depthFunc(n.GEQUAL);break;case Au:n.depthFunc(n.GREATER);break;case Ru:n.depthFunc(n.NOTEQUAL);break;default:n.depthFunc(n.LEQUAL)}we=ae}},setLocked:function(ae){W=ae},setClear:function(ae){xe!==ae&&(xe=ae,pe&&(ae=1-ae),n.clearDepth(ae))},reset:function(){W=!1,ie=null,we=null,xe=null,pe=!1}}}function i(){let W=!1,pe=null,ie=null,we=null,xe=null,ae=null,Pe=null,Ke=null,st=null;return{setTest:function(Qe){W||(Qe?Z(n.STENCIL_TEST):fe(n.STENCIL_TEST))},setMask:function(Qe){pe!==Qe&&!W&&(n.stencilMask(Qe),pe=Qe)},setFunc:function(Qe,Ht,jt){(ie!==Qe||we!==Ht||xe!==jt)&&(n.stencilFunc(Qe,Ht,jt),ie=Qe,we=Ht,xe=jt)},setOp:function(Qe,Ht,jt){(ae!==Qe||Pe!==Ht||Ke!==jt)&&(n.stencilOp(Qe,Ht,jt),ae=Qe,Pe=Ht,Ke=jt)},setLocked:function(Qe){W=Qe},setClear:function(Qe){st!==Qe&&(n.clearStencil(Qe),st=Qe)},reset:function(){W=!1,pe=null,ie=null,we=null,xe=null,ae=null,Pe=null,Ke=null,st=null}}}const s=new t,a=new r,o=new i,l=new WeakMap,c=new WeakMap;let u={},f={},h={},d=new WeakMap,m=[],g=null,p=!1,_=null,M=null,y=null,v=null,S=null,b=null,E=null,x=new lt(0,0,0),w=0,R=!1,L=null,A=null,U=null,P=null,I=null;const F=n.getParameter(n.MAX_COMBINED_TEXTURE_IMAGE_UNITS);let O=!1,q=0;const z=n.getParameter(n.VERSION);z.indexOf("WebGL")!==-1?(q=parseFloat(/^WebGL (\d)/.exec(z)[1]),O=q>=1):z.indexOf("OpenGL ES")!==-1&&(q=parseFloat(/^OpenGL ES (\d)/.exec(z)[1]),O=q>=2);let k=null,N={};const G=n.getParameter(n.SCISSOR_BOX),K=n.getParameter(n.VIEWPORT),J=new Ct().fromArray(G),j=new Ct().fromArray(K);function V(W,pe,ie,we){const xe=new Uint8Array(4),ae=n.createTexture();n.bindTexture(W,ae),n.texParameteri(W,n.TEXTURE_MIN_FILTER,n.NEAREST),n.texParameteri(W,n.TEXTURE_MAG_FILTER,n.NEAREST);for(let Pe=0;Pe<ie;Pe++)W===n.TEXTURE_3D||W===n.TEXTURE_2D_ARRAY?n.texImage3D(pe,0,n.RGBA,1,1,we,0,n.RGBA,n.UNSIGNED_BYTE,xe):n.texImage2D(pe+Pe,0,n.RGBA,1,1,0,n.RGBA,n.UNSIGNED_BYTE,xe);return ae}const Y={};Y[n.TEXTURE_2D]=V(n.TEXTURE_2D,n.TEXTURE_2D,1),Y[n.TEXTURE_CUBE_MAP]=V(n.TEXTURE_CUBE_MAP,n.TEXTURE_CUBE_MAP_POSITIVE_X,6),Y[n.TEXTURE_2D_ARRAY]=V(n.TEXTURE_2D_ARRAY,n.TEXTURE_2D_ARRAY,1,1),Y[n.TEXTURE_3D]=V(n.TEXTURE_3D,n.TEXTURE_3D,1,1),s.setClear(0,0,0,1),a.setClear(1),o.setClear(0),Z(n.DEPTH_TEST),a.setFunc(Ns),ze(!1),ge(jf),Z(n.CULL_FACE),Ae(Sn);function Z(W){u[W]!==!0&&(n.enable(W),u[W]=!0)}function fe(W){u[W]!==!1&&(n.disable(W),u[W]=!1)}function _e(W,pe){return h[W]!==pe?(n.bindFramebuffer(W,pe),h[W]=pe,W===n.DRAW_FRAMEBUFFER&&(h[n.FRAMEBUFFER]=pe),W===n.FRAMEBUFFER&&(h[n.DRAW_FRAMEBUFFER]=pe),!0):!1}function le(W,pe){let ie=m,we=!1;if(W){ie=d.get(pe),ie===void 0&&(ie=[],d.set(pe,ie));const xe=W.textures;if(ie.length!==xe.length||ie[0]!==n.COLOR_ATTACHMENT0){for(let ae=0,Pe=xe.length;ae<Pe;ae++)ie[ae]=n.COLOR_ATTACHMENT0+ae;ie.length=xe.length,we=!0}}else ie[0]!==n.BACK&&(ie[0]=n.BACK,we=!0);we&&n.drawBuffers(ie)}function de(W){return g!==W?(n.useProgram(W),g=W,!0):!1}const Fe={[Nr]:n.FUNC_ADD,[Yg]:n.FUNC_SUBTRACT,[qg]:n.FUNC_REVERSE_SUBTRACT};Fe[jg]=n.MIN,Fe[Kg]=n.MAX;const Ne={[Zg]:n.ZERO,[$g]:n.ONE,[Jg]:n.SRC_COLOR,[Su]:n.SRC_ALPHA,[r_]:n.SRC_ALPHA_SATURATE,[n_]:n.DST_COLOR,[e_]:n.DST_ALPHA,[Qg]:n.ONE_MINUS_SRC_COLOR,[bu]:n.ONE_MINUS_SRC_ALPHA,[i_]:n.ONE_MINUS_DST_COLOR,[t_]:n.ONE_MINUS_DST_ALPHA,[s_]:n.CONSTANT_COLOR,[a_]:n.ONE_MINUS_CONSTANT_COLOR,[o_]:n.CONSTANT_ALPHA,[l_]:n.ONE_MINUS_CONSTANT_ALPHA};function Ae(W,pe,ie,we,xe,ae,Pe,Ke,st,Qe){if(W===Sn){p===!0&&(fe(n.BLEND),p=!1);return}if(p===!1&&(Z(n.BLEND),p=!0),W!==Xg){if(W!==_||Qe!==R){if((M!==Nr||S!==Nr)&&(n.blendEquation(n.FUNC_ADD),M=Nr,S=Nr),Qe)switch(W){case zr:n.blendFuncSeparate(n.ONE,n.ONE_MINUS_SRC_ALPHA,n.ONE,n.ONE_MINUS_SRC_ALPHA);break;case nl:n.blendFunc(n.ONE,n.ONE);break;case Kf:n.blendFuncSeparate(n.ZERO,n.ONE_MINUS_SRC_COLOR,n.ZERO,n.ONE);break;case Zf:n.blendFuncSeparate(n.DST_COLOR,n.ONE_MINUS_SRC_ALPHA,n.ZERO,n.ONE);break;default:ft("WebGLState: Invalid blending: ",W);break}else switch(W){case zr:n.blendFuncSeparate(n.SRC_ALPHA,n.ONE_MINUS_SRC_ALPHA,n.ONE,n.ONE_MINUS_SRC_ALPHA);break;case nl:n.blendFuncSeparate(n.SRC_ALPHA,n.ONE,n.ONE,n.ONE);break;case Kf:ft("WebGLState: SubtractiveBlending requires material.premultipliedAlpha = true");break;case Zf:ft("WebGLState: MultiplyBlending requires material.premultipliedAlpha = true");break;default:ft("WebGLState: Invalid blending: ",W);break}y=null,v=null,b=null,E=null,x.set(0,0,0),w=0,_=W,R=Qe}return}xe=xe||pe,ae=ae||ie,Pe=Pe||we,(pe!==M||xe!==S)&&(n.blendEquationSeparate(Fe[pe],Fe[xe]),M=pe,S=xe),(ie!==y||we!==v||ae!==b||Pe!==E)&&(n.blendFuncSeparate(Ne[ie],Ne[we],Ne[ae],Ne[Pe]),y=ie,v=we,b=ae,E=Pe),(Ke.equals(x)===!1||st!==w)&&(n.blendColor(Ke.r,Ke.g,Ke.b,st),x.copy(Ke),w=st),_=W,R=!1}function be(W,pe){W.side===wn?fe(n.CULL_FACE):Z(n.CULL_FACE);let ie=W.side===sn;pe&&(ie=!ie),ze(ie),W.blending===zr&&W.transparent===!1?Ae(Sn):Ae(W.blending,W.blendEquation,W.blendSrc,W.blendDst,W.blendEquationAlpha,W.blendSrcAlpha,W.blendDstAlpha,W.blendColor,W.blendAlpha,W.premultipliedAlpha),a.setFunc(W.depthFunc),a.setTest(W.depthTest),a.setMask(W.depthWrite),s.setMask(W.colorWrite);const we=W.stencilWrite;o.setTest(we),we&&(o.setMask(W.stencilWriteMask),o.setFunc(W.stencilFunc,W.stencilRef,W.stencilFuncMask),o.setOp(W.stencilFail,W.stencilZFail,W.stencilZPass)),B(W.polygonOffset,W.polygonOffsetFactor,W.polygonOffsetUnits),W.alphaToCoverage===!0?Z(n.SAMPLE_ALPHA_TO_COVERAGE):fe(n.SAMPLE_ALPHA_TO_COVERAGE)}function ze(W){L!==W&&(W?n.frontFace(n.CW):n.frontFace(n.CCW),L=W)}function ge(W){W!==Hg?(Z(n.CULL_FACE),W!==A&&(W===jf?n.cullFace(n.BACK):W===Vg?n.cullFace(n.FRONT):n.cullFace(n.FRONT_AND_BACK))):fe(n.CULL_FACE),A=W}function ke(W){W!==U&&(O&&n.lineWidth(W),U=W)}function B(W,pe,ie){W?(Z(n.POLYGON_OFFSET_FILL),(P!==pe||I!==ie)&&(P=pe,I=ie,a.getReversed()&&(pe=-pe),n.polygonOffset(pe,ie))):fe(n.POLYGON_OFFSET_FILL)}function ue(W){W?Z(n.SCISSOR_TEST):fe(n.SCISSOR_TEST)}function De(W){W===void 0&&(W=n.TEXTURE0+F-1),k!==W&&(n.activeTexture(W),k=W)}function ye(W,pe,ie){ie===void 0&&(k===null?ie=n.TEXTURE0+F-1:ie=k);let we=N[ie];we===void 0&&(we={type:void 0,texture:void 0},N[ie]=we),(we.type!==W||we.texture!==pe)&&(k!==ie&&(n.activeTexture(ie),k=ie),n.bindTexture(W,pe||Y[W]),we.type=W,we.texture=pe)}function ce(){const W=N[k];W!==void 0&&W.type!==void 0&&(n.bindTexture(W.type,null),W.type=void 0,W.texture=void 0)}function Te(){try{n.compressedTexImage2D(...arguments)}catch(W){ft("WebGLState:",W)}}function D(){try{n.compressedTexImage3D(...arguments)}catch(W){ft("WebGLState:",W)}}function T(){try{n.texSubImage2D(...arguments)}catch(W){ft("WebGLState:",W)}}function H(){try{n.texSubImage3D(...arguments)}catch(W){ft("WebGLState:",W)}}function Q(){try{n.compressedTexSubImage2D(...arguments)}catch(W){ft("WebGLState:",W)}}function oe(){try{n.compressedTexSubImage3D(...arguments)}catch(W){ft("WebGLState:",W)}}function me(){try{n.texStorage2D(...arguments)}catch(W){ft("WebGLState:",W)}}function Me(){try{n.texStorage3D(...arguments)}catch(W){ft("WebGLState:",W)}}function ee(){try{n.texImage2D(...arguments)}catch(W){ft("WebGLState:",W)}}function re(){try{n.texImage3D(...arguments)}catch(W){ft("WebGLState:",W)}}function he(W){return f[W]!==void 0?f[W]:n.getParameter(W)}function Re(W,pe){f[W]!==pe&&(n.pixelStorei(W,pe),f[W]=pe)}function ve(W){J.equals(W)===!1&&(n.scissor(W.x,W.y,W.z,W.w),J.copy(W))}function Se(W){j.equals(W)===!1&&(n.viewport(W.x,W.y,W.z,W.w),j.copy(W))}function Ge(W,pe){let ie=c.get(pe);ie===void 0&&(ie=new WeakMap,c.set(pe,ie));let we=ie.get(W);we===void 0&&(we=n.getUniformBlockIndex(pe,W.name),ie.set(W,we))}function Ce(W,pe){const we=c.get(pe).get(W);l.get(pe)!==we&&(n.uniformBlockBinding(pe,we,W.__bindingPointIndex),l.set(pe,we))}function Ye(){n.disable(n.BLEND),n.disable(n.CULL_FACE),n.disable(n.DEPTH_TEST),n.disable(n.POLYGON_OFFSET_FILL),n.disable(n.SCISSOR_TEST),n.disable(n.STENCIL_TEST),n.disable(n.SAMPLE_ALPHA_TO_COVERAGE),n.blendEquation(n.FUNC_ADD),n.blendFunc(n.ONE,n.ZERO),n.blendFuncSeparate(n.ONE,n.ZERO,n.ONE,n.ZERO),n.blendColor(0,0,0,0),n.colorMask(!0,!0,!0,!0),n.clearColor(0,0,0,0),n.depthMask(!0),n.depthFunc(n.LESS),a.setReversed(!1),n.clearDepth(1),n.stencilMask(4294967295),n.stencilFunc(n.ALWAYS,0,4294967295),n.stencilOp(n.KEEP,n.KEEP,n.KEEP),n.clearStencil(0),n.cullFace(n.BACK),n.frontFace(n.CCW),n.polygonOffset(0,0),n.activeTexture(n.TEXTURE0),n.bindFramebuffer(n.FRAMEBUFFER,null),n.bindFramebuffer(n.DRAW_FRAMEBUFFER,null),n.bindFramebuffer(n.READ_FRAMEBUFFER,null),n.useProgram(null),n.lineWidth(1),n.scissor(0,0,n.canvas.width,n.canvas.height),n.viewport(0,0,n.canvas.width,n.canvas.height),n.pixelStorei(n.PACK_ALIGNMENT,4),n.pixelStorei(n.UNPACK_ALIGNMENT,4),n.pixelStorei(n.UNPACK_FLIP_Y_WEBGL,!1),n.pixelStorei(n.UNPACK_PREMULTIPLY_ALPHA_WEBGL,!1),n.pixelStorei(n.UNPACK_COLORSPACE_CONVERSION_WEBGL,n.BROWSER_DEFAULT_WEBGL),n.pixelStorei(n.PACK_ROW_LENGTH,0),n.pixelStorei(n.PACK_SKIP_PIXELS,0),n.pixelStorei(n.PACK_SKIP_ROWS,0),n.pixelStorei(n.UNPACK_ROW_LENGTH,0),n.pixelStorei(n.UNPACK_IMAGE_HEIGHT,0),n.pixelStorei(n.UNPACK_SKIP_PIXELS,0),n.pixelStorei(n.UNPACK_SKIP_ROWS,0),n.pixelStorei(n.UNPACK_SKIP_IMAGES,0),u={},f={},k=null,N={},h={},d=new WeakMap,m=[],g=null,p=!1,_=null,M=null,y=null,v=null,S=null,b=null,E=null,x=new lt(0,0,0),w=0,R=!1,L=null,A=null,U=null,P=null,I=null,J.set(0,0,n.canvas.width,n.canvas.height),j.set(0,0,n.canvas.width,n.canvas.height),s.reset(),a.reset(),o.reset()}return{buffers:{color:s,depth:a,stencil:o},enable:Z,disable:fe,bindFramebuffer:_e,drawBuffers:le,useProgram:de,setBlending:Ae,setMaterial:be,setFlipSided:ze,setCullFace:ge,setLineWidth:ke,setPolygonOffset:B,setScissorTest:ue,activeTexture:De,bindTexture:ye,unbindTexture:ce,compressedTexImage2D:Te,compressedTexImage3D:D,texImage2D:ee,texImage3D:re,pixelStorei:Re,getParameter:he,updateUBOMapping:Ge,uniformBlockBinding:Ce,texStorage2D:me,texStorage3D:Me,texSubImage2D:T,texSubImage3D:H,compressedTexSubImage2D:Q,compressedTexSubImage3D:oe,scissor:ve,viewport:Se,reset:Ye}}function qS(n,e,t,r,i,s,a){const o=e.has("WEBGL_multisampled_render_to_texture")?e.get("WEBGL_multisampled_render_to_texture"):null,l=typeof navigator>"u"?!1:/OculusBrowser/g.test(navigator.userAgent),c=new We,u=new WeakMap,f=new Set;let h;const d=new WeakMap;let m=!1;try{m=typeof OffscreenCanvas<"u"&&new OffscreenCanvas(1,1).getContext("2d")!==null}catch{}function g(D,T){return m?new OffscreenCanvas(D,T):ll("canvas")}function p(D,T,H){let Q=1;const oe=Te(D);if((oe.width>H||oe.height>H)&&(Q=H/Math.max(oe.width,oe.height)),Q<1)if(typeof HTMLImageElement<"u"&&D instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&D instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&D instanceof ImageBitmap||typeof VideoFrame<"u"&&D instanceof VideoFrame){const me=Math.floor(Q*oe.width),Me=Math.floor(Q*oe.height);h===void 0&&(h=g(me,Me));const ee=T?g(me,Me):h;return ee.width=me,ee.height=Me,ee.getContext("2d").drawImage(D,0,0,me,Me),$e("WebGLRenderer: Texture has been resized from ("+oe.width+"x"+oe.height+") to ("+me+"x"+Me+")."),ee}else return"data"in D&&$e("WebGLRenderer: Image in DataTexture is too big ("+oe.width+"x"+oe.height+")."),D;return D}function _(D){return D.generateMipmaps}function M(D){n.generateMipmap(D)}function y(D){return D.isWebGLCubeRenderTarget?n.TEXTURE_CUBE_MAP:D.isWebGL3DRenderTarget?n.TEXTURE_3D:D.isWebGLArrayRenderTarget||D.isCompressedArrayTexture?n.TEXTURE_2D_ARRAY:n.TEXTURE_2D}function v(D,T,H,Q,oe,me=!1){if(D!==null){if(n[D]!==void 0)return n[D];$e("WebGLRenderer: Attempt to use non-existing WebGL internal format '"+D+"'")}let Me;Q&&(Me=e.get("EXT_texture_norm16"),Me||$e("WebGLRenderer: Unable to use normalized textures without EXT_texture_norm16 extension"));let ee=T;if(T===n.RED&&(H===n.FLOAT&&(ee=n.R32F),H===n.HALF_FLOAT&&(ee=n.R16F),H===n.UNSIGNED_BYTE&&(ee=n.R8),H===n.UNSIGNED_SHORT&&Me&&(ee=Me.R16_EXT),H===n.SHORT&&Me&&(ee=Me.R16_SNORM_EXT)),T===n.RED_INTEGER&&(H===n.UNSIGNED_BYTE&&(ee=n.R8UI),H===n.UNSIGNED_SHORT&&(ee=n.R16UI),H===n.UNSIGNED_INT&&(ee=n.R32UI),H===n.BYTE&&(ee=n.R8I),H===n.SHORT&&(ee=n.R16I),H===n.INT&&(ee=n.R32I)),T===n.RG&&(H===n.FLOAT&&(ee=n.RG32F),H===n.HALF_FLOAT&&(ee=n.RG16F),H===n.UNSIGNED_BYTE&&(ee=n.RG8),H===n.UNSIGNED_SHORT&&Me&&(ee=Me.RG16_EXT),H===n.SHORT&&Me&&(ee=Me.RG16_SNORM_EXT)),T===n.RG_INTEGER&&(H===n.UNSIGNED_BYTE&&(ee=n.RG8UI),H===n.UNSIGNED_SHORT&&(ee=n.RG16UI),H===n.UNSIGNED_INT&&(ee=n.RG32UI),H===n.BYTE&&(ee=n.RG8I),H===n.SHORT&&(ee=n.RG16I),H===n.INT&&(ee=n.RG32I)),T===n.RGB_INTEGER&&(H===n.UNSIGNED_BYTE&&(ee=n.RGB8UI),H===n.UNSIGNED_SHORT&&(ee=n.RGB16UI),H===n.UNSIGNED_INT&&(ee=n.RGB32UI),H===n.BYTE&&(ee=n.RGB8I),H===n.SHORT&&(ee=n.RGB16I),H===n.INT&&(ee=n.RGB32I)),T===n.RGBA_INTEGER&&(H===n.UNSIGNED_BYTE&&(ee=n.RGBA8UI),H===n.UNSIGNED_SHORT&&(ee=n.RGBA16UI),H===n.UNSIGNED_INT&&(ee=n.RGBA32UI),H===n.BYTE&&(ee=n.RGBA8I),H===n.SHORT&&(ee=n.RGBA16I),H===n.INT&&(ee=n.RGBA32I)),T===n.RGB&&(H===n.UNSIGNED_SHORT&&Me&&(ee=Me.RGB16_EXT),H===n.SHORT&&Me&&(ee=Me.RGB16_SNORM_EXT),H===n.UNSIGNED_INT_5_9_9_9_REV&&(ee=n.RGB9_E5),H===n.UNSIGNED_INT_10F_11F_11F_REV&&(ee=n.R11F_G11F_B10F)),T===n.RGBA){const re=me?al:ut.getTransfer(oe);H===n.FLOAT&&(ee=n.RGBA32F),H===n.HALF_FLOAT&&(ee=n.RGBA16F),H===n.UNSIGNED_BYTE&&(ee=re===xt?n.SRGB8_ALPHA8:n.RGBA8),H===n.UNSIGNED_SHORT&&Me&&(ee=Me.RGBA16_EXT),H===n.SHORT&&Me&&(ee=Me.RGBA16_SNORM_EXT),H===n.UNSIGNED_SHORT_4_4_4_4&&(ee=n.RGBA4),H===n.UNSIGNED_SHORT_5_5_5_1&&(ee=n.RGB5_A1)}return(ee===n.R16F||ee===n.R32F||ee===n.RG16F||ee===n.RG32F||ee===n.RGBA16F||ee===n.RGBA32F)&&e.get("EXT_color_buffer_float"),ee}function S(D,T){let H;return D?T===null||T===Di||T===Bs?H=n.DEPTH24_STENCIL8:T===li?H=n.DEPTH32F_STENCIL8:T===Oa&&(H=n.DEPTH24_STENCIL8,$e("DepthTexture: 16 bit depth attachment is not supported with stencil. Using 24-bit attachment.")):T===null||T===Di||T===Bs?H=n.DEPTH_COMPONENT24:T===li?H=n.DEPTH_COMPONENT32F:T===Oa&&(H=n.DEPTH_COMPONENT16),H}function b(D,T){return _(D)===!0||D.isFramebufferTexture&&D.minFilter!==cn&&D.minFilter!==zt?Math.log2(Math.max(T.width,T.height))+1:D.mipmaps!==void 0&&D.mipmaps.length>0?D.mipmaps.length:D.isCompressedTexture&&Array.isArray(D.image)?T.mipmaps.length:1}function E(D){const T=D.target;T.removeEventListener("dispose",E),w(T),T.isVideoTexture&&u.delete(T),T.isHTMLTexture&&f.delete(T)}function x(D){const T=D.target;T.removeEventListener("dispose",x),L(T)}function w(D){const T=r.get(D);if(T.__webglInit===void 0)return;const H=D.source,Q=d.get(H);if(Q){const oe=Q[T.__cacheKey];oe.usedTimes--,oe.usedTimes===0&&R(D),Object.keys(Q).length===0&&d.delete(H)}r.remove(D)}function R(D){const T=r.get(D);n.deleteTexture(T.__webglTexture);const H=D.source,Q=d.get(H);delete Q[T.__cacheKey],a.memory.textures--}function L(D){const T=r.get(D);if(D.depthTexture&&(D.depthTexture.dispose(),r.remove(D.depthTexture)),D.isWebGLCubeRenderTarget)for(let Q=0;Q<6;Q++){if(Array.isArray(T.__webglFramebuffer[Q]))for(let oe=0;oe<T.__webglFramebuffer[Q].length;oe++)n.deleteFramebuffer(T.__webglFramebuffer[Q][oe]);else n.deleteFramebuffer(T.__webglFramebuffer[Q]);T.__webglDepthbuffer&&n.deleteRenderbuffer(T.__webglDepthbuffer[Q])}else{if(Array.isArray(T.__webglFramebuffer))for(let Q=0;Q<T.__webglFramebuffer.length;Q++)n.deleteFramebuffer(T.__webglFramebuffer[Q]);else n.deleteFramebuffer(T.__webglFramebuffer);if(T.__webglDepthbuffer&&n.deleteRenderbuffer(T.__webglDepthbuffer),T.__webglMultisampledFramebuffer&&n.deleteFramebuffer(T.__webglMultisampledFramebuffer),T.__webglColorRenderbuffer)for(let Q=0;Q<T.__webglColorRenderbuffer.length;Q++)T.__webglColorRenderbuffer[Q]&&n.deleteRenderbuffer(T.__webglColorRenderbuffer[Q]);T.__webglDepthRenderbuffer&&n.deleteRenderbuffer(T.__webglDepthRenderbuffer)}const H=D.textures;for(let Q=0,oe=H.length;Q<oe;Q++){const me=r.get(H[Q]);me.__webglTexture&&(n.deleteTexture(me.__webglTexture),a.memory.textures--),r.remove(H[Q])}r.remove(D)}let A=0;function U(){A=0}function P(){return A}function I(D){A=D}function F(){const D=A;return D>=i.maxTextures&&$e("WebGLTextures: Trying to use "+D+" texture units while this GPU supports only "+i.maxTextures),A+=1,D}function O(D){const T=[];return T.push(D.wrapS),T.push(D.wrapT),T.push(D.wrapR||0),T.push(D.magFilter),T.push(D.minFilter),T.push(D.anisotropy),T.push(D.internalFormat),T.push(D.format),T.push(D.type),T.push(D.generateMipmaps),T.push(D.premultiplyAlpha),T.push(D.flipY),T.push(D.unpackAlignment),T.push(D.colorSpace),T.join()}function q(D,T){const H=r.get(D);if(D.isVideoTexture&&ye(D),D.isRenderTargetTexture===!1&&D.isExternalTexture!==!0&&D.version>0&&H.__version!==D.version){const Q=D.image;if(Q===null)$e("WebGLRenderer: Texture marked for update but no image data found.");else if(Q.complete===!1)$e("WebGLRenderer: Texture marked for update but image is incomplete");else{fe(H,D,T);return}}else D.isExternalTexture&&(H.__webglTexture=D.sourceTexture?D.sourceTexture:null);t.bindTexture(n.TEXTURE_2D,H.__webglTexture,n.TEXTURE0+T)}function z(D,T){const H=r.get(D);if(D.isRenderTargetTexture===!1&&D.version>0&&H.__version!==D.version){fe(H,D,T);return}else D.isExternalTexture&&(H.__webglTexture=D.sourceTexture?D.sourceTexture:null);t.bindTexture(n.TEXTURE_2D_ARRAY,H.__webglTexture,n.TEXTURE0+T)}function k(D,T){const H=r.get(D);if(D.isRenderTargetTexture===!1&&D.version>0&&H.__version!==D.version){fe(H,D,T);return}t.bindTexture(n.TEXTURE_3D,H.__webglTexture,n.TEXTURE0+T)}function N(D,T){const H=r.get(D);if(D.isCubeDepthTexture!==!0&&D.version>0&&H.__version!==D.version){_e(H,D,T);return}t.bindTexture(n.TEXTURE_CUBE_MAP,H.__webglTexture,n.TEXTURE0+T)}const G={[Cu]:n.REPEAT,[Hi]:n.CLAMP_TO_EDGE,[Pu]:n.MIRRORED_REPEAT},K={[cn]:n.NEAREST,[h_]:n.NEAREST_MIPMAP_NEAREST,[so]:n.NEAREST_MIPMAP_LINEAR,[zt]:n.LINEAR,[ic]:n.LINEAR_MIPMAP_NEAREST,[Br]:n.LINEAR_MIPMAP_LINEAR},J={[p_]:n.NEVER,[x_]:n.ALWAYS,[m_]:n.LESS,[jh]:n.LEQUAL,[g_]:n.EQUAL,[Kh]:n.GEQUAL,[__]:n.GREATER,[v_]:n.NOTEQUAL};function j(D,T){if(T.type===li&&e.has("OES_texture_float_linear")===!1&&(T.magFilter===zt||T.magFilter===ic||T.magFilter===so||T.magFilter===Br||T.minFilter===zt||T.minFilter===ic||T.minFilter===so||T.minFilter===Br)&&$e("WebGLRenderer: Unable to use linear filtering with floating point textures. OES_texture_float_linear not supported on this device."),n.texParameteri(D,n.TEXTURE_WRAP_S,G[T.wrapS]),n.texParameteri(D,n.TEXTURE_WRAP_T,G[T.wrapT]),(D===n.TEXTURE_3D||D===n.TEXTURE_2D_ARRAY)&&n.texParameteri(D,n.TEXTURE_WRAP_R,G[T.wrapR]),n.texParameteri(D,n.TEXTURE_MAG_FILTER,K[T.magFilter]),n.texParameteri(D,n.TEXTURE_MIN_FILTER,K[T.minFilter]),T.compareFunction&&(n.texParameteri(D,n.TEXTURE_COMPARE_MODE,n.COMPARE_REF_TO_TEXTURE),n.texParameteri(D,n.TEXTURE_COMPARE_FUNC,J[T.compareFunction])),e.has("EXT_texture_filter_anisotropic")===!0){if(T.magFilter===cn||T.minFilter!==so&&T.minFilter!==Br||T.type===li&&e.has("OES_texture_float_linear")===!1)return;if(T.anisotropy>1||r.get(T).__currentAnisotropy){const H=e.get("EXT_texture_filter_anisotropic");n.texParameterf(D,H.TEXTURE_MAX_ANISOTROPY_EXT,Math.min(T.anisotropy,i.getMaxAnisotropy())),r.get(T).__currentAnisotropy=T.anisotropy}}}function V(D,T){let H=!1;D.__webglInit===void 0&&(D.__webglInit=!0,T.addEventListener("dispose",E));const Q=T.source;let oe=d.get(Q);oe===void 0&&(oe={},d.set(Q,oe));const me=O(T);if(me!==D.__cacheKey){oe[me]===void 0&&(oe[me]={texture:n.createTexture(),usedTimes:0},a.memory.textures++,H=!0),oe[me].usedTimes++;const Me=oe[D.__cacheKey];Me!==void 0&&(oe[D.__cacheKey].usedTimes--,Me.usedTimes===0&&R(T)),D.__cacheKey=me,D.__webglTexture=oe[me].texture}return H}function Y(D,T,H){return Math.floor(Math.floor(D/H)/T)}function Z(D,T,H,Q){const me=D.updateRanges;if(me.length===0)t.texSubImage2D(n.TEXTURE_2D,0,0,0,T.width,T.height,H,Q,T.data);else{me.sort((Re,ve)=>Re.start-ve.start);let Me=0;for(let Re=1;Re<me.length;Re++){const ve=me[Me],Se=me[Re],Ge=ve.start+ve.count,Ce=Y(Se.start,T.width,4),Ye=Y(ve.start,T.width,4);Se.start<=Ge+1&&Ce===Ye&&Y(Se.start+Se.count-1,T.width,4)===Ce?ve.count=Math.max(ve.count,Se.start+Se.count-ve.start):(++Me,me[Me]=Se)}me.length=Me+1;const ee=t.getParameter(n.UNPACK_ROW_LENGTH),re=t.getParameter(n.UNPACK_SKIP_PIXELS),he=t.getParameter(n.UNPACK_SKIP_ROWS);t.pixelStorei(n.UNPACK_ROW_LENGTH,T.width);for(let Re=0,ve=me.length;Re<ve;Re++){const Se=me[Re],Ge=Math.floor(Se.start/4),Ce=Math.ceil(Se.count/4),Ye=Ge%T.width,W=Math.floor(Ge/T.width),pe=Ce,ie=1;t.pixelStorei(n.UNPACK_SKIP_PIXELS,Ye),t.pixelStorei(n.UNPACK_SKIP_ROWS,W),t.texSubImage2D(n.TEXTURE_2D,0,Ye,W,pe,ie,H,Q,T.data)}D.clearUpdateRanges(),t.pixelStorei(n.UNPACK_ROW_LENGTH,ee),t.pixelStorei(n.UNPACK_SKIP_PIXELS,re),t.pixelStorei(n.UNPACK_SKIP_ROWS,he)}}function fe(D,T,H){let Q=n.TEXTURE_2D;(T.isDataArrayTexture||T.isCompressedArrayTexture)&&(Q=n.TEXTURE_2D_ARRAY),T.isData3DTexture&&(Q=n.TEXTURE_3D);const oe=V(D,T),me=T.source;t.bindTexture(Q,D.__webglTexture,n.TEXTURE0+H);const Me=r.get(me);if(me.version!==Me.__version||oe===!0){if(t.activeTexture(n.TEXTURE0+H),(typeof ImageBitmap<"u"&&T.image instanceof ImageBitmap)===!1){const ie=ut.getPrimaries(ut.workingColorSpace),we=T.colorSpace===yi?null:ut.getPrimaries(T.colorSpace),xe=T.colorSpace===yi||ie===we?n.NONE:n.BROWSER_DEFAULT_WEBGL;t.pixelStorei(n.UNPACK_FLIP_Y_WEBGL,T.flipY),t.pixelStorei(n.UNPACK_PREMULTIPLY_ALPHA_WEBGL,T.premultiplyAlpha),t.pixelStorei(n.UNPACK_COLORSPACE_CONVERSION_WEBGL,xe)}t.pixelStorei(n.UNPACK_ALIGNMENT,T.unpackAlignment);let re=p(T.image,!1,i.maxTextureSize);re=ce(T,re);const he=s.convert(T.format,T.colorSpace),Re=s.convert(T.type);let ve=v(T.internalFormat,he,Re,T.normalized,T.colorSpace,T.isVideoTexture);j(Q,T);let Se;const Ge=T.mipmaps,Ce=T.isVideoTexture!==!0,Ye=Me.__version===void 0||oe===!0,W=me.dataReady,pe=b(T,re);if(T.isDepthTexture)ve=S(T.format===cr,T.type),Ye&&(Ce?t.texStorage2D(n.TEXTURE_2D,1,ve,re.width,re.height):t.texImage2D(n.TEXTURE_2D,0,ve,re.width,re.height,0,he,Re,null));else if(T.isDataTexture)if(Ge.length>0){Ce&&Ye&&t.texStorage2D(n.TEXTURE_2D,pe,ve,Ge[0].width,Ge[0].height);for(let ie=0,we=Ge.length;ie<we;ie++)Se=Ge[ie],Ce?W&&t.texSubImage2D(n.TEXTURE_2D,ie,0,0,Se.width,Se.height,he,Re,Se.data):t.texImage2D(n.TEXTURE_2D,ie,ve,Se.width,Se.height,0,he,Re,Se.data);T.generateMipmaps=!1}else Ce?(Ye&&t.texStorage2D(n.TEXTURE_2D,pe,ve,re.width,re.height),W&&Z(T,re,he,Re)):t.texImage2D(n.TEXTURE_2D,0,ve,re.width,re.height,0,he,Re,re.data);else if(T.isCompressedTexture)if(T.isCompressedArrayTexture){Ce&&Ye&&t.texStorage3D(n.TEXTURE_2D_ARRAY,pe,ve,Ge[0].width,Ge[0].height,re.depth);for(let ie=0,we=Ge.length;ie<we;ie++)if(Se=Ge[ie],T.format!==ci)if(he!==null)if(Ce){if(W)if(T.layerUpdates.size>0){const xe=Cd(Se.width,Se.height,T.format,T.type);for(const ae of T.layerUpdates){const Pe=Se.data.subarray(ae*xe/Se.data.BYTES_PER_ELEMENT,(ae+1)*xe/Se.data.BYTES_PER_ELEMENT);t.compressedTexSubImage3D(n.TEXTURE_2D_ARRAY,ie,0,0,ae,Se.width,Se.height,1,he,Pe)}T.clearLayerUpdates()}else t.compressedTexSubImage3D(n.TEXTURE_2D_ARRAY,ie,0,0,0,Se.width,Se.height,re.depth,he,Se.data)}else t.compressedTexImage3D(n.TEXTURE_2D_ARRAY,ie,ve,Se.width,Se.height,re.depth,0,Se.data,0,0);else $e("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()");else Ce?W&&t.texSubImage3D(n.TEXTURE_2D_ARRAY,ie,0,0,0,Se.width,Se.height,re.depth,he,Re,Se.data):t.texImage3D(n.TEXTURE_2D_ARRAY,ie,ve,Se.width,Se.height,re.depth,0,he,Re,Se.data)}else{Ce&&Ye&&t.texStorage2D(n.TEXTURE_2D,pe,ve,Ge[0].width,Ge[0].height);for(let ie=0,we=Ge.length;ie<we;ie++)Se=Ge[ie],T.format!==ci?he!==null?Ce?W&&t.compressedTexSubImage2D(n.TEXTURE_2D,ie,0,0,Se.width,Se.height,he,Se.data):t.compressedTexImage2D(n.TEXTURE_2D,ie,ve,Se.width,Se.height,0,Se.data):$e("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()"):Ce?W&&t.texSubImage2D(n.TEXTURE_2D,ie,0,0,Se.width,Se.height,he,Re,Se.data):t.texImage2D(n.TEXTURE_2D,ie,ve,Se.width,Se.height,0,he,Re,Se.data)}else if(T.isDataArrayTexture)if(Ce){if(Ye&&t.texStorage3D(n.TEXTURE_2D_ARRAY,pe,ve,re.width,re.height,re.depth),W)if(T.layerUpdates.size>0){const ie=Cd(re.width,re.height,T.format,T.type);for(const we of T.layerUpdates){const xe=re.data.subarray(we*ie/re.data.BYTES_PER_ELEMENT,(we+1)*ie/re.data.BYTES_PER_ELEMENT);t.texSubImage3D(n.TEXTURE_2D_ARRAY,0,0,0,we,re.width,re.height,1,he,Re,xe)}T.clearLayerUpdates()}else t.texSubImage3D(n.TEXTURE_2D_ARRAY,0,0,0,0,re.width,re.height,re.depth,he,Re,re.data)}else t.texImage3D(n.TEXTURE_2D_ARRAY,0,ve,re.width,re.height,re.depth,0,he,Re,re.data);else if(T.isData3DTexture)Ce?(Ye&&t.texStorage3D(n.TEXTURE_3D,pe,ve,re.width,re.height,re.depth),W&&t.texSubImage3D(n.TEXTURE_3D,0,0,0,0,re.width,re.height,re.depth,he,Re,re.data)):t.texImage3D(n.TEXTURE_3D,0,ve,re.width,re.height,re.depth,0,he,Re,re.data);else if(T.isFramebufferTexture){if(Ye)if(Ce)t.texStorage2D(n.TEXTURE_2D,pe,ve,re.width,re.height);else{let ie=re.width,we=re.height;for(let xe=0;xe<pe;xe++)t.texImage2D(n.TEXTURE_2D,xe,ve,ie,we,0,he,Re,null),ie>>=1,we>>=1}}else if(T.isHTMLTexture){if("texElementImage2D"in n){const ie=n.canvas;if(ie.hasAttribute("layoutsubtree")||ie.setAttribute("layoutsubtree","true"),re.parentNode!==ie){ie.appendChild(re),f.add(T),ie.onpaint=Ke=>{const st=Ke.changedElements;for(const Qe of f)st.includes(Qe.image)&&(Qe.needsUpdate=!0)},ie.requestPaint();return}const we=0,xe=n.RGBA,ae=n.RGBA,Pe=n.UNSIGNED_BYTE;n.texElementImage2D(n.TEXTURE_2D,we,xe,ae,Pe,re),n.texParameteri(n.TEXTURE_2D,n.TEXTURE_MIN_FILTER,n.LINEAR),n.texParameteri(n.TEXTURE_2D,n.TEXTURE_WRAP_S,n.CLAMP_TO_EDGE),n.texParameteri(n.TEXTURE_2D,n.TEXTURE_WRAP_T,n.CLAMP_TO_EDGE)}}else if(Ge.length>0){if(Ce&&Ye){const ie=Te(Ge[0]);t.texStorage2D(n.TEXTURE_2D,pe,ve,ie.width,ie.height)}for(let ie=0,we=Ge.length;ie<we;ie++)Se=Ge[ie],Ce?W&&t.texSubImage2D(n.TEXTURE_2D,ie,0,0,he,Re,Se):t.texImage2D(n.TEXTURE_2D,ie,ve,he,Re,Se);T.generateMipmaps=!1}else if(Ce){if(Ye){const ie=Te(re);t.texStorage2D(n.TEXTURE_2D,pe,ve,ie.width,ie.height)}W&&t.texSubImage2D(n.TEXTURE_2D,0,0,0,he,Re,re)}else t.texImage2D(n.TEXTURE_2D,0,ve,he,Re,re);_(T)&&M(Q),Me.__version=me.version,T.onUpdate&&T.onUpdate(T)}D.__version=T.version}function _e(D,T,H){if(T.image.length!==6)return;const Q=V(D,T),oe=T.source;t.bindTexture(n.TEXTURE_CUBE_MAP,D.__webglTexture,n.TEXTURE0+H);const me=r.get(oe);if(oe.version!==me.__version||Q===!0){t.activeTexture(n.TEXTURE0+H);const Me=ut.getPrimaries(ut.workingColorSpace),ee=T.colorSpace===yi?null:ut.getPrimaries(T.colorSpace),re=T.colorSpace===yi||Me===ee?n.NONE:n.BROWSER_DEFAULT_WEBGL;t.pixelStorei(n.UNPACK_FLIP_Y_WEBGL,T.flipY),t.pixelStorei(n.UNPACK_PREMULTIPLY_ALPHA_WEBGL,T.premultiplyAlpha),t.pixelStorei(n.UNPACK_ALIGNMENT,T.unpackAlignment),t.pixelStorei(n.UNPACK_COLORSPACE_CONVERSION_WEBGL,re);const he=T.isCompressedTexture||T.image[0].isCompressedTexture,Re=T.image[0]&&T.image[0].isDataTexture,ve=[];for(let ae=0;ae<6;ae++)!he&&!Re?ve[ae]=p(T.image[ae],!0,i.maxCubemapSize):ve[ae]=Re?T.image[ae].image:T.image[ae],ve[ae]=ce(T,ve[ae]);const Se=ve[0],Ge=s.convert(T.format,T.colorSpace),Ce=s.convert(T.type),Ye=v(T.internalFormat,Ge,Ce,T.normalized,T.colorSpace),W=T.isVideoTexture!==!0,pe=me.__version===void 0||Q===!0,ie=oe.dataReady;let we=b(T,Se);j(n.TEXTURE_CUBE_MAP,T);let xe;if(he){W&&pe&&t.texStorage2D(n.TEXTURE_CUBE_MAP,we,Ye,Se.width,Se.height);for(let ae=0;ae<6;ae++){xe=ve[ae].mipmaps;for(let Pe=0;Pe<xe.length;Pe++){const Ke=xe[Pe];T.format!==ci?Ge!==null?W?ie&&t.compressedTexSubImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ae,Pe,0,0,Ke.width,Ke.height,Ge,Ke.data):t.compressedTexImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ae,Pe,Ye,Ke.width,Ke.height,0,Ke.data):$e("WebGLRenderer: Attempt to load unsupported compressed texture format in .setTextureCube()"):W?ie&&t.texSubImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ae,Pe,0,0,Ke.width,Ke.height,Ge,Ce,Ke.data):t.texImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ae,Pe,Ye,Ke.width,Ke.height,0,Ge,Ce,Ke.data)}}}else{if(xe=T.mipmaps,W&&pe){xe.length>0&&we++;const ae=Te(ve[0]);t.texStorage2D(n.TEXTURE_CUBE_MAP,we,Ye,ae.width,ae.height)}for(let ae=0;ae<6;ae++)if(Re){W?ie&&t.texSubImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ae,0,0,0,ve[ae].width,ve[ae].height,Ge,Ce,ve[ae].data):t.texImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ae,0,Ye,ve[ae].width,ve[ae].height,0,Ge,Ce,ve[ae].data);for(let Pe=0;Pe<xe.length;Pe++){const st=xe[Pe].image[ae].image;W?ie&&t.texSubImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ae,Pe+1,0,0,st.width,st.height,Ge,Ce,st.data):t.texImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ae,Pe+1,Ye,st.width,st.height,0,Ge,Ce,st.data)}}else{W?ie&&t.texSubImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ae,0,0,0,Ge,Ce,ve[ae]):t.texImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ae,0,Ye,Ge,Ce,ve[ae]);for(let Pe=0;Pe<xe.length;Pe++){const Ke=xe[Pe];W?ie&&t.texSubImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ae,Pe+1,0,0,Ge,Ce,Ke.image[ae]):t.texImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+ae,Pe+1,Ye,Ge,Ce,Ke.image[ae])}}}_(T)&&M(n.TEXTURE_CUBE_MAP),me.__version=oe.version,T.onUpdate&&T.onUpdate(T)}D.__version=T.version}function le(D,T,H,Q,oe,me){const Me=s.convert(H.format,H.colorSpace),ee=s.convert(H.type),re=v(H.internalFormat,Me,ee,H.normalized,H.colorSpace),he=r.get(T),Re=r.get(H);if(Re.__renderTarget=T,!he.__hasExternalTextures){const ve=Math.max(1,T.width>>me),Se=Math.max(1,T.height>>me);oe===n.TEXTURE_3D||oe===n.TEXTURE_2D_ARRAY?t.texImage3D(oe,me,re,ve,Se,T.depth,0,Me,ee,null):t.texImage2D(oe,me,re,ve,Se,0,Me,ee,null)}t.bindFramebuffer(n.FRAMEBUFFER,D),De(T)?o.framebufferTexture2DMultisampleEXT(n.FRAMEBUFFER,Q,oe,Re.__webglTexture,0,ue(T)):(oe===n.TEXTURE_2D||oe>=n.TEXTURE_CUBE_MAP_POSITIVE_X&&oe<=n.TEXTURE_CUBE_MAP_NEGATIVE_Z)&&n.framebufferTexture2D(n.FRAMEBUFFER,Q,oe,Re.__webglTexture,me),t.bindFramebuffer(n.FRAMEBUFFER,null)}function de(D,T,H){if(n.bindRenderbuffer(n.RENDERBUFFER,D),T.depthBuffer){const Q=T.depthTexture,oe=Q&&Q.isDepthTexture?Q.type:null,me=S(T.stencilBuffer,oe),Me=T.stencilBuffer?n.DEPTH_STENCIL_ATTACHMENT:n.DEPTH_ATTACHMENT;De(T)?o.renderbufferStorageMultisampleEXT(n.RENDERBUFFER,ue(T),me,T.width,T.height):H?n.renderbufferStorageMultisample(n.RENDERBUFFER,ue(T),me,T.width,T.height):n.renderbufferStorage(n.RENDERBUFFER,me,T.width,T.height),n.framebufferRenderbuffer(n.FRAMEBUFFER,Me,n.RENDERBUFFER,D)}else{const Q=T.textures;for(let oe=0;oe<Q.length;oe++){const me=Q[oe],Me=s.convert(me.format,me.colorSpace),ee=s.convert(me.type),re=v(me.internalFormat,Me,ee,me.normalized,me.colorSpace);De(T)?o.renderbufferStorageMultisampleEXT(n.RENDERBUFFER,ue(T),re,T.width,T.height):H?n.renderbufferStorageMultisample(n.RENDERBUFFER,ue(T),re,T.width,T.height):n.renderbufferStorage(n.RENDERBUFFER,re,T.width,T.height)}}n.bindRenderbuffer(n.RENDERBUFFER,null)}function Fe(D,T,H){const Q=T.isWebGLCubeRenderTarget===!0;if(t.bindFramebuffer(n.FRAMEBUFFER,D),!(T.depthTexture&&T.depthTexture.isDepthTexture))throw new Error("renderTarget.depthTexture must be an instance of THREE.DepthTexture");const oe=r.get(T.depthTexture);if(oe.__renderTarget=T,(!oe.__webglTexture||T.depthTexture.image.width!==T.width||T.depthTexture.image.height!==T.height)&&(T.depthTexture.image.width=T.width,T.depthTexture.image.height=T.height,T.depthTexture.needsUpdate=!0),Q){if(oe.__webglInit===void 0&&(oe.__webglInit=!0,T.depthTexture.addEventListener("dispose",E)),oe.__webglTexture===void 0){oe.__webglTexture=n.createTexture(),t.bindTexture(n.TEXTURE_CUBE_MAP,oe.__webglTexture),j(n.TEXTURE_CUBE_MAP,T.depthTexture);const he=s.convert(T.depthTexture.format),Re=s.convert(T.depthTexture.type);let ve;T.depthTexture.format===qi?ve=n.DEPTH_COMPONENT24:T.depthTexture.format===cr&&(ve=n.DEPTH24_STENCIL8);for(let Se=0;Se<6;Se++)n.texImage2D(n.TEXTURE_CUBE_MAP_POSITIVE_X+Se,0,ve,T.width,T.height,0,he,Re,null)}}else q(T.depthTexture,0);const me=oe.__webglTexture,Me=ue(T),ee=Q?n.TEXTURE_CUBE_MAP_POSITIVE_X+H:n.TEXTURE_2D,re=T.depthTexture.format===cr?n.DEPTH_STENCIL_ATTACHMENT:n.DEPTH_ATTACHMENT;if(T.depthTexture.format===qi)De(T)?o.framebufferTexture2DMultisampleEXT(n.FRAMEBUFFER,re,ee,me,0,Me):n.framebufferTexture2D(n.FRAMEBUFFER,re,ee,me,0);else if(T.depthTexture.format===cr)De(T)?o.framebufferTexture2DMultisampleEXT(n.FRAMEBUFFER,re,ee,me,0,Me):n.framebufferTexture2D(n.FRAMEBUFFER,re,ee,me,0);else throw new Error("Unknown depthTexture format")}function Ne(D){const T=r.get(D),H=D.isWebGLCubeRenderTarget===!0;if(T.__boundDepthTexture!==D.depthTexture){const Q=D.depthTexture;if(T.__depthDisposeCallback&&T.__depthDisposeCallback(),Q){const oe=()=>{delete T.__boundDepthTexture,delete T.__depthDisposeCallback,Q.removeEventListener("dispose",oe)};Q.addEventListener("dispose",oe),T.__depthDisposeCallback=oe}T.__boundDepthTexture=Q}if(D.depthTexture&&!T.__autoAllocateDepthBuffer)if(H)for(let Q=0;Q<6;Q++)Fe(T.__webglFramebuffer[Q],D,Q);else{const Q=D.texture.mipmaps;Q&&Q.length>0?Fe(T.__webglFramebuffer[0],D,0):Fe(T.__webglFramebuffer,D,0)}else if(H){T.__webglDepthbuffer=[];for(let Q=0;Q<6;Q++)if(t.bindFramebuffer(n.FRAMEBUFFER,T.__webglFramebuffer[Q]),T.__webglDepthbuffer[Q]===void 0)T.__webglDepthbuffer[Q]=n.createRenderbuffer(),de(T.__webglDepthbuffer[Q],D,!1);else{const oe=D.stencilBuffer?n.DEPTH_STENCIL_ATTACHMENT:n.DEPTH_ATTACHMENT,me=T.__webglDepthbuffer[Q];n.bindRenderbuffer(n.RENDERBUFFER,me),n.framebufferRenderbuffer(n.FRAMEBUFFER,oe,n.RENDERBUFFER,me)}}else{const Q=D.texture.mipmaps;if(Q&&Q.length>0?t.bindFramebuffer(n.FRAMEBUFFER,T.__webglFramebuffer[0]):t.bindFramebuffer(n.FRAMEBUFFER,T.__webglFramebuffer),T.__webglDepthbuffer===void 0)T.__webglDepthbuffer=n.createRenderbuffer(),de(T.__webglDepthbuffer,D,!1);else{const oe=D.stencilBuffer?n.DEPTH_STENCIL_ATTACHMENT:n.DEPTH_ATTACHMENT,me=T.__webglDepthbuffer;n.bindRenderbuffer(n.RENDERBUFFER,me),n.framebufferRenderbuffer(n.FRAMEBUFFER,oe,n.RENDERBUFFER,me)}}t.bindFramebuffer(n.FRAMEBUFFER,null)}function Ae(D,T,H){const Q=r.get(D);T!==void 0&&le(Q.__webglFramebuffer,D,D.texture,n.COLOR_ATTACHMENT0,n.TEXTURE_2D,0),H!==void 0&&Ne(D)}function be(D){const T=D.texture,H=r.get(D),Q=r.get(T);D.addEventListener("dispose",x);const oe=D.textures,me=D.isWebGLCubeRenderTarget===!0,Me=oe.length>1;if(Me||(Q.__webglTexture===void 0&&(Q.__webglTexture=n.createTexture()),Q.__version=T.version,a.memory.textures++),me){H.__webglFramebuffer=[];for(let ee=0;ee<6;ee++)if(T.mipmaps&&T.mipmaps.length>0){H.__webglFramebuffer[ee]=[];for(let re=0;re<T.mipmaps.length;re++)H.__webglFramebuffer[ee][re]=n.createFramebuffer()}else H.__webglFramebuffer[ee]=n.createFramebuffer()}else{if(T.mipmaps&&T.mipmaps.length>0){H.__webglFramebuffer=[];for(let ee=0;ee<T.mipmaps.length;ee++)H.__webglFramebuffer[ee]=n.createFramebuffer()}else H.__webglFramebuffer=n.createFramebuffer();if(Me)for(let ee=0,re=oe.length;ee<re;ee++){const he=r.get(oe[ee]);he.__webglTexture===void 0&&(he.__webglTexture=n.createTexture(),a.memory.textures++)}if(D.samples>0&&De(D)===!1){H.__webglMultisampledFramebuffer=n.createFramebuffer(),H.__webglColorRenderbuffer=[],t.bindFramebuffer(n.FRAMEBUFFER,H.__webglMultisampledFramebuffer);for(let ee=0;ee<oe.length;ee++){const re=oe[ee];H.__webglColorRenderbuffer[ee]=n.createRenderbuffer(),n.bindRenderbuffer(n.RENDERBUFFER,H.__webglColorRenderbuffer[ee]);const he=s.convert(re.format,re.colorSpace),Re=s.convert(re.type),ve=v(re.internalFormat,he,Re,re.normalized,re.colorSpace,D.isXRRenderTarget===!0),Se=ue(D);n.renderbufferStorageMultisample(n.RENDERBUFFER,Se,ve,D.width,D.height),n.framebufferRenderbuffer(n.FRAMEBUFFER,n.COLOR_ATTACHMENT0+ee,n.RENDERBUFFER,H.__webglColorRenderbuffer[ee])}n.bindRenderbuffer(n.RENDERBUFFER,null),D.depthBuffer&&(H.__webglDepthRenderbuffer=n.createRenderbuffer(),de(H.__webglDepthRenderbuffer,D,!0)),t.bindFramebuffer(n.FRAMEBUFFER,null)}}if(me){t.bindTexture(n.TEXTURE_CUBE_MAP,Q.__webglTexture),j(n.TEXTURE_CUBE_MAP,T);for(let ee=0;ee<6;ee++)if(T.mipmaps&&T.mipmaps.length>0)for(let re=0;re<T.mipmaps.length;re++)le(H.__webglFramebuffer[ee][re],D,T,n.COLOR_ATTACHMENT0,n.TEXTURE_CUBE_MAP_POSITIVE_X+ee,re);else le(H.__webglFramebuffer[ee],D,T,n.COLOR_ATTACHMENT0,n.TEXTURE_CUBE_MAP_POSITIVE_X+ee,0);_(T)&&M(n.TEXTURE_CUBE_MAP),t.unbindTexture()}else if(Me){for(let ee=0,re=oe.length;ee<re;ee++){const he=oe[ee],Re=r.get(he);let ve=n.TEXTURE_2D;(D.isWebGL3DRenderTarget||D.isWebGLArrayRenderTarget)&&(ve=D.isWebGL3DRenderTarget?n.TEXTURE_3D:n.TEXTURE_2D_ARRAY),t.bindTexture(ve,Re.__webglTexture),j(ve,he),le(H.__webglFramebuffer,D,he,n.COLOR_ATTACHMENT0+ee,ve,0),_(he)&&M(ve)}t.unbindTexture()}else{let ee=n.TEXTURE_2D;if((D.isWebGL3DRenderTarget||D.isWebGLArrayRenderTarget)&&(ee=D.isWebGL3DRenderTarget?n.TEXTURE_3D:n.TEXTURE_2D_ARRAY),t.bindTexture(ee,Q.__webglTexture),j(ee,T),T.mipmaps&&T.mipmaps.length>0)for(let re=0;re<T.mipmaps.length;re++)le(H.__webglFramebuffer[re],D,T,n.COLOR_ATTACHMENT0,ee,re);else le(H.__webglFramebuffer,D,T,n.COLOR_ATTACHMENT0,ee,0);_(T)&&M(ee),t.unbindTexture()}D.depthBuffer&&Ne(D)}function ze(D){const T=D.textures;for(let H=0,Q=T.length;H<Q;H++){const oe=T[H];if(_(oe)){const me=y(D),Me=r.get(oe).__webglTexture;t.bindTexture(me,Me),M(me),t.unbindTexture()}}}const ge=[],ke=[];function B(D){if(D.samples>0){if(De(D)===!1){const T=D.textures,H=D.width,Q=D.height;let oe=n.COLOR_BUFFER_BIT;const me=D.stencilBuffer?n.DEPTH_STENCIL_ATTACHMENT:n.DEPTH_ATTACHMENT,Me=r.get(D),ee=T.length>1;if(ee)for(let he=0;he<T.length;he++)t.bindFramebuffer(n.FRAMEBUFFER,Me.__webglMultisampledFramebuffer),n.framebufferRenderbuffer(n.FRAMEBUFFER,n.COLOR_ATTACHMENT0+he,n.RENDERBUFFER,null),t.bindFramebuffer(n.FRAMEBUFFER,Me.__webglFramebuffer),n.framebufferTexture2D(n.DRAW_FRAMEBUFFER,n.COLOR_ATTACHMENT0+he,n.TEXTURE_2D,null,0);t.bindFramebuffer(n.READ_FRAMEBUFFER,Me.__webglMultisampledFramebuffer);const re=D.texture.mipmaps;re&&re.length>0?t.bindFramebuffer(n.DRAW_FRAMEBUFFER,Me.__webglFramebuffer[0]):t.bindFramebuffer(n.DRAW_FRAMEBUFFER,Me.__webglFramebuffer);for(let he=0;he<T.length;he++){if(D.resolveDepthBuffer&&(D.depthBuffer&&(oe|=n.DEPTH_BUFFER_BIT),D.stencilBuffer&&D.resolveStencilBuffer&&(oe|=n.STENCIL_BUFFER_BIT)),ee){n.framebufferRenderbuffer(n.READ_FRAMEBUFFER,n.COLOR_ATTACHMENT0,n.RENDERBUFFER,Me.__webglColorRenderbuffer[he]);const Re=r.get(T[he]).__webglTexture;n.framebufferTexture2D(n.DRAW_FRAMEBUFFER,n.COLOR_ATTACHMENT0,n.TEXTURE_2D,Re,0)}n.blitFramebuffer(0,0,H,Q,0,0,H,Q,oe,n.NEAREST),l===!0&&(ge.length=0,ke.length=0,ge.push(n.COLOR_ATTACHMENT0+he),D.depthBuffer&&D.resolveDepthBuffer===!1&&(ge.push(me),ke.push(me),n.invalidateFramebuffer(n.DRAW_FRAMEBUFFER,ke)),n.invalidateFramebuffer(n.READ_FRAMEBUFFER,ge))}if(t.bindFramebuffer(n.READ_FRAMEBUFFER,null),t.bindFramebuffer(n.DRAW_FRAMEBUFFER,null),ee)for(let he=0;he<T.length;he++){t.bindFramebuffer(n.FRAMEBUFFER,Me.__webglMultisampledFramebuffer),n.framebufferRenderbuffer(n.FRAMEBUFFER,n.COLOR_ATTACHMENT0+he,n.RENDERBUFFER,Me.__webglColorRenderbuffer[he]);const Re=r.get(T[he]).__webglTexture;t.bindFramebuffer(n.FRAMEBUFFER,Me.__webglFramebuffer),n.framebufferTexture2D(n.DRAW_FRAMEBUFFER,n.COLOR_ATTACHMENT0+he,n.TEXTURE_2D,Re,0)}t.bindFramebuffer(n.DRAW_FRAMEBUFFER,Me.__webglMultisampledFramebuffer)}else if(D.depthBuffer&&D.resolveDepthBuffer===!1&&l){const T=D.stencilBuffer?n.DEPTH_STENCIL_ATTACHMENT:n.DEPTH_ATTACHMENT;n.invalidateFramebuffer(n.DRAW_FRAMEBUFFER,[T])}}}function ue(D){return Math.min(i.maxSamples,D.samples)}function De(D){const T=r.get(D);return D.samples>0&&e.has("WEBGL_multisampled_render_to_texture")===!0&&T.__useRenderToTexture!==!1}function ye(D){const T=a.render.frame;u.get(D)!==T&&(u.set(D,T),D.update())}function ce(D,T){const H=D.colorSpace,Q=D.format,oe=D.type;return D.isCompressedTexture===!0||D.isVideoTexture===!0||H!==ks&&H!==yi&&(ut.getTransfer(H)===xt?(Q!==ci||oe!==Yt)&&$e("WebGLTextures: sRGB encoded textures have to use RGBAFormat and UnsignedByteType."):ft("WebGLTextures: Unsupported texture color space:",H)),T}function Te(D){return typeof HTMLImageElement<"u"&&D instanceof HTMLImageElement?(c.width=D.naturalWidth||D.width,c.height=D.naturalHeight||D.height):typeof VideoFrame<"u"&&D instanceof VideoFrame?(c.width=D.displayWidth,c.height=D.displayHeight):(c.width=D.width,c.height=D.height),c}this.allocateTextureUnit=F,this.resetTextureUnits=U,this.getTextureUnits=P,this.setTextureUnits=I,this.setTexture2D=q,this.setTexture2DArray=z,this.setTexture3D=k,this.setTextureCube=N,this.rebindTextures=Ae,this.setupRenderTarget=be,this.updateRenderTargetMipmap=ze,this.updateMultisampleRenderTarget=B,this.setupDepthRenderbuffer=Ne,this.setupFrameBufferTexture=le,this.useMultisampledRTT=De,this.isReversedDepthBuffer=function(){return t.buffers.depth.getReversed()}}function jS(n,e){function t(r,i=yi){let s;const a=ut.getTransfer(i);if(r===Yt)return n.UNSIGNED_BYTE;if(r===Vh)return n.UNSIGNED_SHORT_4_4_4_4;if(r===Wh)return n.UNSIGNED_SHORT_5_5_5_1;if(r===Sm)return n.UNSIGNED_INT_5_9_9_9_REV;if(r===bm)return n.UNSIGNED_INT_10F_11F_11F_REV;if(r===xm)return n.BYTE;if(r===Mm)return n.SHORT;if(r===Oa)return n.UNSIGNED_SHORT;if(r===Hh)return n.INT;if(r===Di)return n.UNSIGNED_INT;if(r===li)return n.FLOAT;if(r===Yi)return n.HALF_FLOAT;if(r===ym)return n.ALPHA;if(r===Tm)return n.RGB;if(r===ci)return n.RGBA;if(r===qi)return n.DEPTH_COMPONENT;if(r===cr)return n.DEPTH_STENCIL;if(r===Em)return n.RED;if(r===Xh)return n.RED_INTEGER;if(r===Kr)return n.RG;if(r===Yh)return n.RG_INTEGER;if(r===qh)return n.RGBA_INTEGER;if(r===Wo||r===Xo||r===Yo||r===qo)if(a===xt)if(s=e.get("WEBGL_compressed_texture_s3tc_srgb"),s!==null){if(r===Wo)return s.COMPRESSED_SRGB_S3TC_DXT1_EXT;if(r===Xo)return s.COMPRESSED_SRGB_ALPHA_S3TC_DXT1_EXT;if(r===Yo)return s.COMPRESSED_SRGB_ALPHA_S3TC_DXT3_EXT;if(r===qo)return s.COMPRESSED_SRGB_ALPHA_S3TC_DXT5_EXT}else return null;else if(s=e.get("WEBGL_compressed_texture_s3tc"),s!==null){if(r===Wo)return s.COMPRESSED_RGB_S3TC_DXT1_EXT;if(r===Xo)return s.COMPRESSED_RGBA_S3TC_DXT1_EXT;if(r===Yo)return s.COMPRESSED_RGBA_S3TC_DXT3_EXT;if(r===qo)return s.COMPRESSED_RGBA_S3TC_DXT5_EXT}else return null;if(r===Du||r===Uu||r===Lu||r===Iu)if(s=e.get("WEBGL_compressed_texture_pvrtc"),s!==null){if(r===Du)return s.COMPRESSED_RGB_PVRTC_4BPPV1_IMG;if(r===Uu)return s.COMPRESSED_RGB_PVRTC_2BPPV1_IMG;if(r===Lu)return s.COMPRESSED_RGBA_PVRTC_4BPPV1_IMG;if(r===Iu)return s.COMPRESSED_RGBA_PVRTC_2BPPV1_IMG}else return null;if(r===Fu||r===Nu||r===Ou||r===Bu||r===ku||r===rl||r===zu)if(s=e.get("WEBGL_compressed_texture_etc"),s!==null){if(r===Fu||r===Nu)return a===xt?s.COMPRESSED_SRGB8_ETC2:s.COMPRESSED_RGB8_ETC2;if(r===Ou)return a===xt?s.COMPRESSED_SRGB8_ALPHA8_ETC2_EAC:s.COMPRESSED_RGBA8_ETC2_EAC;if(r===Bu)return s.COMPRESSED_R11_EAC;if(r===ku)return s.COMPRESSED_SIGNED_R11_EAC;if(r===rl)return s.COMPRESSED_RG11_EAC;if(r===zu)return s.COMPRESSED_SIGNED_RG11_EAC}else return null;if(r===Gu||r===Hu||r===Vu||r===Wu||r===Xu||r===Yu||r===qu||r===ju||r===Ku||r===Zu||r===$u||r===Ju||r===Qu||r===eh)if(s=e.get("WEBGL_compressed_texture_astc"),s!==null){if(r===Gu)return a===xt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR:s.COMPRESSED_RGBA_ASTC_4x4_KHR;if(r===Hu)return a===xt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR:s.COMPRESSED_RGBA_ASTC_5x4_KHR;if(r===Vu)return a===xt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR:s.COMPRESSED_RGBA_ASTC_5x5_KHR;if(r===Wu)return a===xt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR:s.COMPRESSED_RGBA_ASTC_6x5_KHR;if(r===Xu)return a===xt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR:s.COMPRESSED_RGBA_ASTC_6x6_KHR;if(r===Yu)return a===xt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR:s.COMPRESSED_RGBA_ASTC_8x5_KHR;if(r===qu)return a===xt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR:s.COMPRESSED_RGBA_ASTC_8x6_KHR;if(r===ju)return a===xt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR:s.COMPRESSED_RGBA_ASTC_8x8_KHR;if(r===Ku)return a===xt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR:s.COMPRESSED_RGBA_ASTC_10x5_KHR;if(r===Zu)return a===xt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR:s.COMPRESSED_RGBA_ASTC_10x6_KHR;if(r===$u)return a===xt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR:s.COMPRESSED_RGBA_ASTC_10x8_KHR;if(r===Ju)return a===xt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR:s.COMPRESSED_RGBA_ASTC_10x10_KHR;if(r===Qu)return a===xt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR:s.COMPRESSED_RGBA_ASTC_12x10_KHR;if(r===eh)return a===xt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR:s.COMPRESSED_RGBA_ASTC_12x12_KHR}else return null;if(r===th||r===nh||r===ih)if(s=e.get("EXT_texture_compression_bptc"),s!==null){if(r===th)return a===xt?s.COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT:s.COMPRESSED_RGBA_BPTC_UNORM_EXT;if(r===nh)return s.COMPRESSED_RGB_BPTC_SIGNED_FLOAT_EXT;if(r===ih)return s.COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT_EXT}else return null;if(r===rh||r===sh||r===sl||r===ah)if(s=e.get("EXT_texture_compression_rgtc"),s!==null){if(r===rh)return s.COMPRESSED_RED_RGTC1_EXT;if(r===sh)return s.COMPRESSED_SIGNED_RED_RGTC1_EXT;if(r===sl)return s.COMPRESSED_RED_GREEN_RGTC2_EXT;if(r===ah)return s.COMPRESSED_SIGNED_RED_GREEN_RGTC2_EXT}else return null;return r===Bs?n.UNSIGNED_INT_24_8:n[r]!==void 0?n[r]:null}return{convert:t}}const KS=`
void main() {

	gl_Position = vec4( position, 1.0 );

}`,ZS=`
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

}`;class $S{constructor(){this.texture=null,this.mesh=null,this.depthNear=0,this.depthFar=0}init(e,t){if(this.texture===null){const r=new Fm(e.texture);(e.depthNear!==t.depthNear||e.depthFar!==t.depthFar)&&(this.depthNear=e.depthNear,this.depthFar=e.depthFar),this.texture=r}}getMesh(e){if(this.texture!==null&&this.mesh===null){const t=e.cameras[0].viewport,r=new an({vertexShader:KS,fragmentShader:ZS,uniforms:{depthColor:{value:this.texture},depthWidth:{value:t.z},depthHeight:{value:t.w}}});this.mesh=new Wn(new $r(20,20),r)}return this.mesh}reset(){this.texture=null,this.mesh=null}getDepthTexture(){return this.texture}}class JS extends hi{constructor(e,t){super();const r=this;let i=null,s=1,a=null,o="local-floor",l=1,c=null,u=null,f=null,h=null,d=null,m=null;const g=typeof XRWebGLBinding<"u",p=new $S,_={},M=t.getContextAttributes();let y=null,v=null;const S=[],b=[],E=new We;let x=null;const w=new kn;w.viewport=new Ct;const R=new kn;R.viewport=new Ct;const L=[w,R],A=new av;let U=null,P=null;this.cameraAutoUpdate=!0,this.enabled=!1,this.isPresenting=!1,this.getController=function(V){let Y=S[V];return Y===void 0&&(Y=new uc,S[V]=Y),Y.getTargetRaySpace()},this.getControllerGrip=function(V){let Y=S[V];return Y===void 0&&(Y=new uc,S[V]=Y),Y.getGripSpace()},this.getHand=function(V){let Y=S[V];return Y===void 0&&(Y=new uc,S[V]=Y),Y.getHandSpace()};function I(V){const Y=b.indexOf(V.inputSource);if(Y===-1)return;const Z=S[Y];Z!==void 0&&(Z.update(V.inputSource,V.frame,c||a),Z.dispatchEvent({type:V.type,data:V.inputSource}))}function F(){i.removeEventListener("select",I),i.removeEventListener("selectstart",I),i.removeEventListener("selectend",I),i.removeEventListener("squeeze",I),i.removeEventListener("squeezestart",I),i.removeEventListener("squeezeend",I),i.removeEventListener("end",F),i.removeEventListener("inputsourceschange",O);for(let V=0;V<S.length;V++){const Y=b[V];Y!==null&&(b[V]=null,S[V].disconnect(Y))}U=null,P=null,p.reset();for(const V in _)delete _[V];e.setRenderTarget(y),d=null,h=null,f=null,i=null,v=null,j.stop(),r.isPresenting=!1,e.setPixelRatio(x),e.setSize(E.width,E.height,!1),r.dispatchEvent({type:"sessionend"})}this.setFramebufferScaleFactor=function(V){s=V,r.isPresenting===!0&&$e("WebXRManager: Cannot change framebuffer scale while presenting.")},this.setReferenceSpaceType=function(V){o=V,r.isPresenting===!0&&$e("WebXRManager: Cannot change reference space type while presenting.")},this.getReferenceSpace=function(){return c||a},this.setReferenceSpace=function(V){c=V},this.getBaseLayer=function(){return h!==null?h:d},this.getBinding=function(){return f===null&&g&&(f=new XRWebGLBinding(i,t)),f},this.getFrame=function(){return m},this.getSession=function(){return i},this.setSession=async function(V){if(i=V,i!==null){if(y=e.getRenderTarget(),i.addEventListener("select",I),i.addEventListener("selectstart",I),i.addEventListener("selectend",I),i.addEventListener("squeeze",I),i.addEventListener("squeezestart",I),i.addEventListener("squeezeend",I),i.addEventListener("end",F),i.addEventListener("inputsourceschange",O),M.xrCompatible!==!0&&await t.makeXRCompatible(),x=e.getPixelRatio(),e.getSize(E),g&&"createProjectionLayer"in XRWebGLBinding.prototype){let Z=null,fe=null,_e=null;M.depth&&(_e=M.stencil?t.DEPTH24_STENCIL8:t.DEPTH_COMPONENT24,Z=M.stencil?cr:qi,fe=M.stencil?Bs:Di);const le={colorFormat:t.RGBA8,depthFormat:_e,scaleFactor:s};f=this.getBinding(),h=f.createProjectionLayer(le),i.updateRenderState({layers:[h]}),e.setPixelRatio(1),e.setSize(h.textureWidth,h.textureHeight,!1),v=new $t(h.textureWidth,h.textureHeight,{format:ci,type:Yt,depthTexture:new Wi(h.textureWidth,h.textureHeight,fe,void 0,void 0,void 0,void 0,void 0,void 0,Z),stencilBuffer:M.stencil,colorSpace:e.outputColorSpace,samples:M.antialias?4:0,resolveDepthBuffer:h.ignoreDepthValues===!1,resolveStencilBuffer:h.ignoreDepthValues===!1})}else{const Z={antialias:M.antialias,alpha:!0,depth:M.depth,stencil:M.stencil,framebufferScaleFactor:s};d=new XRWebGLLayer(i,t,Z),i.updateRenderState({baseLayer:d}),e.setPixelRatio(1),e.setSize(d.framebufferWidth,d.framebufferHeight,!1),v=new $t(d.framebufferWidth,d.framebufferHeight,{format:ci,type:Yt,colorSpace:e.outputColorSpace,stencilBuffer:M.stencil,resolveDepthBuffer:d.ignoreDepthValues===!1,resolveStencilBuffer:d.ignoreDepthValues===!1})}v.isXRRenderTarget=!0,this.setFoveation(l),c=null,a=await i.requestReferenceSpace(o),j.setContext(i),j.start(),r.isPresenting=!0,r.dispatchEvent({type:"sessionstart"})}},this.getEnvironmentBlendMode=function(){if(i!==null)return i.environmentBlendMode},this.getDepthTexture=function(){return p.getDepthTexture()};function O(V){for(let Y=0;Y<V.removed.length;Y++){const Z=V.removed[Y],fe=b.indexOf(Z);fe>=0&&(b[fe]=null,S[fe].disconnect(Z))}for(let Y=0;Y<V.added.length;Y++){const Z=V.added[Y];let fe=b.indexOf(Z);if(fe===-1){for(let le=0;le<S.length;le++)if(le>=b.length){b.push(Z),fe=le;break}else if(b[le]===null){b[le]=Z,fe=le;break}if(fe===-1)break}const _e=S[fe];_e&&_e.connect(Z)}}const q=new X,z=new X;function k(V,Y,Z){q.setFromMatrixPosition(Y.matrixWorld),z.setFromMatrixPosition(Z.matrixWorld);const fe=q.distanceTo(z),_e=Y.projectionMatrix.elements,le=Z.projectionMatrix.elements,de=_e[14]/(_e[10]-1),Fe=_e[14]/(_e[10]+1),Ne=(_e[9]+1)/_e[5],Ae=(_e[9]-1)/_e[5],be=(_e[8]-1)/_e[0],ze=(le[8]+1)/le[0],ge=de*be,ke=de*ze,B=fe/(-be+ze),ue=B*-be;if(Y.matrixWorld.decompose(V.position,V.quaternion,V.scale),V.translateX(ue),V.translateZ(B),V.matrixWorld.compose(V.position,V.quaternion,V.scale),V.matrixWorldInverse.copy(V.matrixWorld).invert(),_e[10]===-1)V.projectionMatrix.copy(Y.projectionMatrix),V.projectionMatrixInverse.copy(Y.projectionMatrixInverse);else{const De=de+B,ye=Fe+B,ce=ge-ue,Te=ke+(fe-ue),D=Ne*Fe/ye*De,T=Ae*Fe/ye*De;V.projectionMatrix.makePerspective(ce,Te,D,T,De,ye),V.projectionMatrixInverse.copy(V.projectionMatrix).invert()}}function N(V,Y){Y===null?V.matrixWorld.copy(V.matrix):V.matrixWorld.multiplyMatrices(Y.matrixWorld,V.matrix),V.matrixWorldInverse.copy(V.matrixWorld).invert()}this.updateCamera=function(V){if(i===null)return;let Y=V.near,Z=V.far;p.texture!==null&&(p.depthNear>0&&(Y=p.depthNear),p.depthFar>0&&(Z=p.depthFar)),A.near=R.near=w.near=Y,A.far=R.far=w.far=Z,(U!==A.near||P!==A.far)&&(i.updateRenderState({depthNear:A.near,depthFar:A.far}),U=A.near,P=A.far),A.layers.mask=V.layers.mask|6,w.layers.mask=A.layers.mask&-5,R.layers.mask=A.layers.mask&-3;const fe=V.parent,_e=A.cameras;N(A,fe);for(let le=0;le<_e.length;le++)N(_e[le],fe);_e.length===2?k(A,w,R):A.projectionMatrix.copy(w.projectionMatrix),G(V,A,fe)};function G(V,Y,Z){Z===null?V.matrix.copy(Y.matrixWorld):(V.matrix.copy(Z.matrixWorld),V.matrix.invert(),V.matrix.multiply(Y.matrixWorld)),V.matrix.decompose(V.position,V.quaternion,V.scale),V.updateMatrixWorld(!0),V.projectionMatrix.copy(Y.projectionMatrix),V.projectionMatrixInverse.copy(Y.projectionMatrixInverse),V.isPerspectiveCamera&&(V.fov=ch*2*Math.atan(1/V.projectionMatrix.elements[5]),V.zoom=1)}this.getCamera=function(){return A},this.getFoveation=function(){if(!(h===null&&d===null))return l},this.setFoveation=function(V){l=V,h!==null&&(h.fixedFoveation=V),d!==null&&d.fixedFoveation!==void 0&&(d.fixedFoveation=V)},this.hasDepthSensing=function(){return p.texture!==null},this.getDepthSensingMesh=function(){return p.getMesh(A)},this.getCameraTexture=function(V){return _[V]};let K=null;function J(V,Y){if(u=Y.getViewerPose(c||a),m=Y,u!==null){const Z=u.views;d!==null&&(e.setRenderTargetFramebuffer(v,d.framebuffer),e.setRenderTarget(v));let fe=!1;Z.length!==A.cameras.length&&(A.cameras.length=0,fe=!0);for(let Fe=0;Fe<Z.length;Fe++){const Ne=Z[Fe];let Ae=null;if(d!==null)Ae=d.getViewport(Ne);else{const ze=f.getViewSubImage(h,Ne);Ae=ze.viewport,Fe===0&&(e.setRenderTargetTextures(v,ze.colorTexture,ze.depthStencilTexture),e.setRenderTarget(v))}let be=L[Fe];be===void 0&&(be=new kn,be.layers.enable(Fe),be.viewport=new Ct,L[Fe]=be),be.matrix.fromArray(Ne.transform.matrix),be.matrix.decompose(be.position,be.quaternion,be.scale),be.projectionMatrix.fromArray(Ne.projectionMatrix),be.projectionMatrixInverse.copy(be.projectionMatrix).invert(),be.viewport.set(Ae.x,Ae.y,Ae.width,Ae.height),Fe===0&&(A.matrix.copy(be.matrix),A.matrix.decompose(A.position,A.quaternion,A.scale)),fe===!0&&A.cameras.push(be)}const _e=i.enabledFeatures;if(_e&&_e.includes("depth-sensing")&&i.depthUsage=="gpu-optimized"&&g){f=r.getBinding();const Fe=f.getDepthInformation(Z[0]);Fe&&Fe.isValid&&Fe.texture&&p.init(Fe,i.renderState)}if(_e&&_e.includes("camera-access")&&g){e.state.unbindTexture(),f=r.getBinding();for(let Fe=0;Fe<Z.length;Fe++){const Ne=Z[Fe].camera;if(Ne){let Ae=_[Ne];Ae||(Ae=new Fm,_[Ne]=Ae);const be=f.getCameraImage(Ne);Ae.sourceTexture=be}}}}for(let Z=0;Z<S.length;Z++){const fe=b[Z],_e=S[Z];fe!==null&&_e!==void 0&&_e.update(fe,Y,c||a)}K&&K(V,Y),Y.detectedPlanes&&r.dispatchEvent({type:"planesdetected",data:Y}),m=null}const j=new Gm;j.setAnimationLoop(J),this.setAnimationLoop=function(V){K=V},this.dispose=function(){}}}const QS=new Ot,jm=new nt;jm.set(-1,0,0,0,1,0,0,0,1);function eb(n,e){function t(p,_){p.matrixAutoUpdate===!0&&p.updateMatrix(),_.value.copy(p.matrix)}function r(p,_){_.color.getRGB(p.fogColor.value,Nm(n)),_.isFog?(p.fogNear.value=_.near,p.fogFar.value=_.far):_.isFogExp2&&(p.fogDensity.value=_.density)}function i(p,_,M,y,v){_.isNodeMaterial?_.uniformsNeedUpdate=!1:_.isMeshBasicMaterial?s(p,_):_.isMeshLambertMaterial?(s(p,_),_.envMap&&(p.envMapIntensity.value=_.envMapIntensity)):_.isMeshToonMaterial?(s(p,_),f(p,_)):_.isMeshPhongMaterial?(s(p,_),u(p,_),_.envMap&&(p.envMapIntensity.value=_.envMapIntensity)):_.isMeshStandardMaterial?(s(p,_),h(p,_),_.isMeshPhysicalMaterial&&d(p,_,v)):_.isMeshMatcapMaterial?(s(p,_),m(p,_)):_.isMeshDepthMaterial?s(p,_):_.isMeshDistanceMaterial?(s(p,_),g(p,_)):_.isMeshNormalMaterial?s(p,_):_.isLineBasicMaterial?(a(p,_),_.isLineDashedMaterial&&o(p,_)):_.isPointsMaterial?l(p,_,M,y):_.isSpriteMaterial?c(p,_):_.isShadowMaterial?(p.color.value.copy(_.color),p.opacity.value=_.opacity):_.isShaderMaterial&&(_.uniformsNeedUpdate=!1)}function s(p,_){p.opacity.value=_.opacity,_.color&&p.diffuse.value.copy(_.color),_.emissive&&p.emissive.value.copy(_.emissive).multiplyScalar(_.emissiveIntensity),_.map&&(p.map.value=_.map,t(_.map,p.mapTransform)),_.alphaMap&&(p.alphaMap.value=_.alphaMap,t(_.alphaMap,p.alphaMapTransform)),_.bumpMap&&(p.bumpMap.value=_.bumpMap,t(_.bumpMap,p.bumpMapTransform),p.bumpScale.value=_.bumpScale,_.side===sn&&(p.bumpScale.value*=-1)),_.normalMap&&(p.normalMap.value=_.normalMap,t(_.normalMap,p.normalMapTransform),p.normalScale.value.copy(_.normalScale),_.side===sn&&p.normalScale.value.negate()),_.displacementMap&&(p.displacementMap.value=_.displacementMap,t(_.displacementMap,p.displacementMapTransform),p.displacementScale.value=_.displacementScale,p.displacementBias.value=_.displacementBias),_.emissiveMap&&(p.emissiveMap.value=_.emissiveMap,t(_.emissiveMap,p.emissiveMapTransform)),_.specularMap&&(p.specularMap.value=_.specularMap,t(_.specularMap,p.specularMapTransform)),_.alphaTest>0&&(p.alphaTest.value=_.alphaTest);const M=e.get(_),y=M.envMap,v=M.envMapRotation;y&&(p.envMap.value=y,p.envMapRotation.value.setFromMatrix4(QS.makeRotationFromEuler(v)).transpose(),y.isCubeTexture&&y.isRenderTargetTexture===!1&&p.envMapRotation.value.premultiply(jm),p.reflectivity.value=_.reflectivity,p.ior.value=_.ior,p.refractionRatio.value=_.refractionRatio),_.lightMap&&(p.lightMap.value=_.lightMap,p.lightMapIntensity.value=_.lightMapIntensity,t(_.lightMap,p.lightMapTransform)),_.aoMap&&(p.aoMap.value=_.aoMap,p.aoMapIntensity.value=_.aoMapIntensity,t(_.aoMap,p.aoMapTransform))}function a(p,_){p.diffuse.value.copy(_.color),p.opacity.value=_.opacity,_.map&&(p.map.value=_.map,t(_.map,p.mapTransform))}function o(p,_){p.dashSize.value=_.dashSize,p.totalSize.value=_.dashSize+_.gapSize,p.scale.value=_.scale}function l(p,_,M,y){p.diffuse.value.copy(_.color),p.opacity.value=_.opacity,p.size.value=_.size*M,p.scale.value=y*.5,_.map&&(p.map.value=_.map,t(_.map,p.uvTransform)),_.alphaMap&&(p.alphaMap.value=_.alphaMap,t(_.alphaMap,p.alphaMapTransform)),_.alphaTest>0&&(p.alphaTest.value=_.alphaTest)}function c(p,_){p.diffuse.value.copy(_.color),p.opacity.value=_.opacity,p.rotation.value=_.rotation,_.map&&(p.map.value=_.map,t(_.map,p.mapTransform)),_.alphaMap&&(p.alphaMap.value=_.alphaMap,t(_.alphaMap,p.alphaMapTransform)),_.alphaTest>0&&(p.alphaTest.value=_.alphaTest)}function u(p,_){p.specular.value.copy(_.specular),p.shininess.value=Math.max(_.shininess,1e-4)}function f(p,_){_.gradientMap&&(p.gradientMap.value=_.gradientMap)}function h(p,_){p.metalness.value=_.metalness,_.metalnessMap&&(p.metalnessMap.value=_.metalnessMap,t(_.metalnessMap,p.metalnessMapTransform)),p.roughness.value=_.roughness,_.roughnessMap&&(p.roughnessMap.value=_.roughnessMap,t(_.roughnessMap,p.roughnessMapTransform)),_.envMap&&(p.envMapIntensity.value=_.envMapIntensity)}function d(p,_,M){p.ior.value=_.ior,_.sheen>0&&(p.sheenColor.value.copy(_.sheenColor).multiplyScalar(_.sheen),p.sheenRoughness.value=_.sheenRoughness,_.sheenColorMap&&(p.sheenColorMap.value=_.sheenColorMap,t(_.sheenColorMap,p.sheenColorMapTransform)),_.sheenRoughnessMap&&(p.sheenRoughnessMap.value=_.sheenRoughnessMap,t(_.sheenRoughnessMap,p.sheenRoughnessMapTransform))),_.clearcoat>0&&(p.clearcoat.value=_.clearcoat,p.clearcoatRoughness.value=_.clearcoatRoughness,_.clearcoatMap&&(p.clearcoatMap.value=_.clearcoatMap,t(_.clearcoatMap,p.clearcoatMapTransform)),_.clearcoatRoughnessMap&&(p.clearcoatRoughnessMap.value=_.clearcoatRoughnessMap,t(_.clearcoatRoughnessMap,p.clearcoatRoughnessMapTransform)),_.clearcoatNormalMap&&(p.clearcoatNormalMap.value=_.clearcoatNormalMap,t(_.clearcoatNormalMap,p.clearcoatNormalMapTransform),p.clearcoatNormalScale.value.copy(_.clearcoatNormalScale),_.side===sn&&p.clearcoatNormalScale.value.negate())),_.dispersion>0&&(p.dispersion.value=_.dispersion),_.iridescence>0&&(p.iridescence.value=_.iridescence,p.iridescenceIOR.value=_.iridescenceIOR,p.iridescenceThicknessMinimum.value=_.iridescenceThicknessRange[0],p.iridescenceThicknessMaximum.value=_.iridescenceThicknessRange[1],_.iridescenceMap&&(p.iridescenceMap.value=_.iridescenceMap,t(_.iridescenceMap,p.iridescenceMapTransform)),_.iridescenceThicknessMap&&(p.iridescenceThicknessMap.value=_.iridescenceThicknessMap,t(_.iridescenceThicknessMap,p.iridescenceThicknessMapTransform))),_.transmission>0&&(p.transmission.value=_.transmission,p.transmissionSamplerMap.value=M.texture,p.transmissionSamplerSize.value.set(M.width,M.height),_.transmissionMap&&(p.transmissionMap.value=_.transmissionMap,t(_.transmissionMap,p.transmissionMapTransform)),p.thickness.value=_.thickness,_.thicknessMap&&(p.thicknessMap.value=_.thicknessMap,t(_.thicknessMap,p.thicknessMapTransform)),p.attenuationDistance.value=_.attenuationDistance,p.attenuationColor.value.copy(_.attenuationColor)),_.anisotropy>0&&(p.anisotropyVector.value.set(_.anisotropy*Math.cos(_.anisotropyRotation),_.anisotropy*Math.sin(_.anisotropyRotation)),_.anisotropyMap&&(p.anisotropyMap.value=_.anisotropyMap,t(_.anisotropyMap,p.anisotropyMapTransform))),p.specularIntensity.value=_.specularIntensity,p.specularColor.value.copy(_.specularColor),_.specularColorMap&&(p.specularColorMap.value=_.specularColorMap,t(_.specularColorMap,p.specularColorMapTransform)),_.specularIntensityMap&&(p.specularIntensityMap.value=_.specularIntensityMap,t(_.specularIntensityMap,p.specularIntensityMapTransform))}function m(p,_){_.matcap&&(p.matcap.value=_.matcap)}function g(p,_){const M=e.get(_).light;p.referencePosition.value.setFromMatrixPosition(M.matrixWorld),p.nearDistance.value=M.shadow.camera.near,p.farDistance.value=M.shadow.camera.far}return{refreshFogUniforms:r,refreshMaterialUniforms:i}}function tb(n,e,t,r){let i={},s={},a=[];const o=n.getParameter(n.MAX_UNIFORM_BUFFER_BINDINGS);function l(M,y){const v=y.program;r.uniformBlockBinding(M,v)}function c(M,y){let v=i[M.id];v===void 0&&(m(M),v=u(M),i[M.id]=v,M.addEventListener("dispose",p));const S=y.program;r.updateUBOMapping(M,S);const b=e.render.frame;s[M.id]!==b&&(h(M),s[M.id]=b)}function u(M){const y=f();M.__bindingPointIndex=y;const v=n.createBuffer(),S=M.__size,b=M.usage;return n.bindBuffer(n.UNIFORM_BUFFER,v),n.bufferData(n.UNIFORM_BUFFER,S,b),n.bindBuffer(n.UNIFORM_BUFFER,null),n.bindBufferBase(n.UNIFORM_BUFFER,y,v),v}function f(){for(let M=0;M<o;M++)if(a.indexOf(M)===-1)return a.push(M),M;return ft("WebGLRenderer: Maximum number of simultaneously usable uniforms groups reached."),0}function h(M){const y=i[M.id],v=M.uniforms,S=M.__cache;n.bindBuffer(n.UNIFORM_BUFFER,y);for(let b=0,E=v.length;b<E;b++){const x=Array.isArray(v[b])?v[b]:[v[b]];for(let w=0,R=x.length;w<R;w++){const L=x[w];if(d(L,b,w,S)===!0){const A=L.__offset,U=Array.isArray(L.value)?L.value:[L.value];let P=0;for(let I=0;I<U.length;I++){const F=U[I],O=g(F);typeof F=="number"||typeof F=="boolean"?(L.__data[0]=F,n.bufferSubData(n.UNIFORM_BUFFER,A+P,L.__data)):F.isMatrix3?(L.__data[0]=F.elements[0],L.__data[1]=F.elements[1],L.__data[2]=F.elements[2],L.__data[3]=0,L.__data[4]=F.elements[3],L.__data[5]=F.elements[4],L.__data[6]=F.elements[5],L.__data[7]=0,L.__data[8]=F.elements[6],L.__data[9]=F.elements[7],L.__data[10]=F.elements[8],L.__data[11]=0):ArrayBuffer.isView(F)?L.__data.set(new F.constructor(F.buffer,F.byteOffset,L.__data.length)):(F.toArray(L.__data,P),P+=O.storage/Float32Array.BYTES_PER_ELEMENT)}n.bufferSubData(n.UNIFORM_BUFFER,A,L.__data)}}}n.bindBuffer(n.UNIFORM_BUFFER,null)}function d(M,y,v,S){const b=M.value,E=y+"_"+v;if(S[E]===void 0)return typeof b=="number"||typeof b=="boolean"?S[E]=b:ArrayBuffer.isView(b)?S[E]=b.slice():S[E]=b.clone(),!0;{const x=S[E];if(typeof b=="number"||typeof b=="boolean"){if(x!==b)return S[E]=b,!0}else{if(ArrayBuffer.isView(b))return!0;if(x.equals(b)===!1)return x.copy(b),!0}}return!1}function m(M){const y=M.uniforms;let v=0;const S=16;for(let E=0,x=y.length;E<x;E++){const w=Array.isArray(y[E])?y[E]:[y[E]];for(let R=0,L=w.length;R<L;R++){const A=w[R],U=Array.isArray(A.value)?A.value:[A.value];for(let P=0,I=U.length;P<I;P++){const F=U[P],O=g(F),q=v%S,z=q%O.boundary,k=q+z;v+=z,k!==0&&S-k<O.storage&&(v+=S-k),A.__data=new Float32Array(O.storage/Float32Array.BYTES_PER_ELEMENT),A.__offset=v,v+=O.storage}}}const b=v%S;return b>0&&(v+=S-b),M.__size=v,M.__cache={},this}function g(M){const y={boundary:0,storage:0};return typeof M=="number"||typeof M=="boolean"?(y.boundary=4,y.storage=4):M.isVector2?(y.boundary=8,y.storage=8):M.isVector3||M.isColor?(y.boundary=16,y.storage=12):M.isVector4?(y.boundary=16,y.storage=16):M.isMatrix3?(y.boundary=48,y.storage=48):M.isMatrix4?(y.boundary=64,y.storage=64):M.isTexture?$e("WebGLRenderer: Texture samplers can not be part of an uniforms group."):ArrayBuffer.isView(M)?(y.boundary=16,y.storage=M.byteLength):$e("WebGLRenderer: Unsupported uniform value type.",M),y}function p(M){const y=M.target;y.removeEventListener("dispose",p);const v=a.indexOf(y.__bindingPointIndex);a.splice(v,1),n.deleteBuffer(i[y.id]),delete i[y.id],delete s[y.id]}function _(){for(const M in i)n.deleteBuffer(i[M]);a=[],i={},s={}}return{bind:l,update:c,dispose:_}}const nb=new Uint16Array([12469,15057,12620,14925,13266,14620,13807,14376,14323,13990,14545,13625,14713,13328,14840,12882,14931,12528,14996,12233,15039,11829,15066,11525,15080,11295,15085,10976,15082,10705,15073,10495,13880,14564,13898,14542,13977,14430,14158,14124,14393,13732,14556,13410,14702,12996,14814,12596,14891,12291,14937,11834,14957,11489,14958,11194,14943,10803,14921,10506,14893,10278,14858,9960,14484,14039,14487,14025,14499,13941,14524,13740,14574,13468,14654,13106,14743,12678,14818,12344,14867,11893,14889,11509,14893,11180,14881,10751,14852,10428,14812,10128,14765,9754,14712,9466,14764,13480,14764,13475,14766,13440,14766,13347,14769,13070,14786,12713,14816,12387,14844,11957,14860,11549,14868,11215,14855,10751,14825,10403,14782,10044,14729,9651,14666,9352,14599,9029,14967,12835,14966,12831,14963,12804,14954,12723,14936,12564,14917,12347,14900,11958,14886,11569,14878,11247,14859,10765,14828,10401,14784,10011,14727,9600,14660,9289,14586,8893,14508,8533,15111,12234,15110,12234,15104,12216,15092,12156,15067,12010,15028,11776,14981,11500,14942,11205,14902,10752,14861,10393,14812,9991,14752,9570,14682,9252,14603,8808,14519,8445,14431,8145,15209,11449,15208,11451,15202,11451,15190,11438,15163,11384,15117,11274,15055,10979,14994,10648,14932,10343,14871,9936,14803,9532,14729,9218,14645,8742,14556,8381,14461,8020,14365,7603,15273,10603,15272,10607,15267,10619,15256,10631,15231,10614,15182,10535,15118,10389,15042,10167,14963,9787,14883,9447,14800,9115,14710,8665,14615,8318,14514,7911,14411,7507,14279,7198,15314,9675,15313,9683,15309,9712,15298,9759,15277,9797,15229,9773,15166,9668,15084,9487,14995,9274,14898,8910,14800,8539,14697,8234,14590,7790,14479,7409,14367,7067,14178,6621,15337,8619,15337,8631,15333,8677,15325,8769,15305,8871,15264,8940,15202,8909,15119,8775,15022,8565,14916,8328,14804,8009,14688,7614,14569,7287,14448,6888,14321,6483,14088,6171,15350,7402,15350,7419,15347,7480,15340,7613,15322,7804,15287,7973,15229,8057,15148,8012,15046,7846,14933,7611,14810,7357,14682,7069,14552,6656,14421,6316,14251,5948,14007,5528,15356,5942,15356,5977,15353,6119,15348,6294,15332,6551,15302,6824,15249,7044,15171,7122,15070,7050,14949,6861,14818,6611,14679,6349,14538,6067,14398,5651,14189,5311,13935,4958,15359,4123,15359,4153,15356,4296,15353,4646,15338,5160,15311,5508,15263,5829,15188,6042,15088,6094,14966,6001,14826,5796,14678,5543,14527,5287,14377,4985,14133,4586,13869,4257,15360,1563,15360,1642,15358,2076,15354,2636,15341,3350,15317,4019,15273,4429,15203,4732,15105,4911,14981,4932,14836,4818,14679,4621,14517,4386,14359,4156,14083,3795,13808,3437,15360,122,15360,137,15358,285,15355,636,15344,1274,15322,2177,15281,2765,15215,3223,15120,3451,14995,3569,14846,3567,14681,3466,14511,3305,14344,3121,14037,2800,13753,2467,15360,0,15360,1,15359,21,15355,89,15346,253,15325,479,15287,796,15225,1148,15133,1492,15008,1749,14856,1882,14685,1886,14506,1783,14324,1608,13996,1398,13702,1183]);let vi=null;function ib(){return vi===null&&(vi=new X_(nb,16,16,Kr,Yi),vi.name="DFG_LUT",vi.minFilter=zt,vi.magFilter=zt,vi.wrapS=Hi,vi.wrapT=Hi,vi.generateMipmaps=!1,vi.needsUpdate=!0),vi}class rb{constructor(e={}){const{canvas:t=S_(),context:r=null,depth:i=!0,stencil:s=!1,alpha:a=!1,antialias:o=!1,premultipliedAlpha:l=!0,preserveDrawingBuffer:c=!1,powerPreference:u="default",failIfMajorPerformanceCaveat:f=!1,reversedDepthBuffer:h=!1,outputBufferType:d=Yt}=e;this.isWebGLRenderer=!0;let m;if(r!==null){if(typeof WebGLRenderingContext<"u"&&r instanceof WebGLRenderingContext)throw new Error("THREE.WebGLRenderer: WebGL 1 is not supported since r163.");m=r.getContextAttributes().alpha}else m=a;const g=d,p=new Set([qh,Yh,Xh]),_=new Set([Yt,Di,Oa,Bs,Vh,Wh]),M=new Uint32Array(4),y=new Int32Array(4),v=new X;let S=null,b=null;const E=[],x=[];let w=null;this.domElement=t,this.debug={checkShaderErrors:!0,onShaderError:null},this.autoClear=!0,this.autoClearColor=!0,this.autoClearDepth=!0,this.autoClearStencil=!0,this.sortObjects=!0,this.clippingPlanes=[],this.localClippingEnabled=!1,this.toneMapping=Pi,this.toneMappingExposure=1,this.transmissionResolutionScale=1;const R=this;let L=!1,A=null;this._outputColorSpace=bt;let U=0,P=0,I=null,F=-1,O=null;const q=new Ct,z=new Ct;let k=null;const N=new lt(0);let G=0,K=t.width,J=t.height,j=1,V=null,Y=null;const Z=new Ct(0,0,K,J),fe=new Ct(0,0,K,J);let _e=!1;const le=new Lm;let de=!1,Fe=!1;const Ne=new Ot,Ae=new X,be=new Ct,ze={background:null,fog:null,environment:null,overrideMaterial:null,isScene:!0};let ge=!1;function ke(){return I===null?j:1}let B=r;function ue(C,$){return t.getContext(C,$)}try{const C={alpha:!0,depth:i,stencil:s,antialias:o,premultipliedAlpha:l,preserveDrawingBuffer:c,powerPreference:u,failIfMajorPerformanceCaveat:f};if("setAttribute"in t&&t.setAttribute("data-engine",`three.js r${qa}`),t.addEventListener("webglcontextlost",ae,!1),t.addEventListener("webglcontextrestored",Pe,!1),t.addEventListener("webglcontextcreationerror",Ke,!1),B===null){const $="webgl2";if(B=ue($,C),B===null)throw ue($)?new Error("Error creating WebGL context with your selected attributes."):new Error("Error creating WebGL context.")}}catch(C){throw ft("WebGLRenderer: "+C.message),C}let De,ye,ce,Te,D,T,H,Q,oe,me,Me,ee,re,he,Re,ve,Se,Ge,Ce,Ye,W,pe,ie;function we(){De=new iM(B),De.init(),W=new jS(B,De),ye=new K1(B,De,e,W),ce=new YS(B,De),ye.reversedDepthBuffer&&h&&ce.buffers.depth.setReversed(!0),Te=new aM(B),D=new US,T=new qS(B,De,ce,D,ye,W,Te),H=new nM(R),Q=new uv(B),pe=new q1(B,Q),oe=new rM(B,Q,Te,pe),me=new lM(B,oe,Q,pe,Te),Ge=new oM(B,ye,T),Re=new Z1(D),Me=new DS(R,H,De,ye,pe,Re),ee=new eb(R,D),re=new IS,he=new zS(De),Se=new Y1(R,H,ce,me,m,l),ve=new XS(R,me,ye),ie=new tb(B,Te,ye,ce),Ce=new j1(B,De,Te),Ye=new sM(B,De,Te),Te.programs=Me.programs,R.capabilities=ye,R.extensions=De,R.properties=D,R.renderLists=re,R.shadowMap=ve,R.state=ce,R.info=Te}we(),g!==Yt&&(w=new uM(g,t.width,t.height,i,s));const xe=new JS(R,B);this.xr=xe,this.getContext=function(){return B},this.getContextAttributes=function(){return B.getContextAttributes()},this.forceContextLoss=function(){const C=De.get("WEBGL_lose_context");C&&C.loseContext()},this.forceContextRestore=function(){const C=De.get("WEBGL_lose_context");C&&C.restoreContext()},this.getPixelRatio=function(){return j},this.setPixelRatio=function(C){C!==void 0&&(j=C,this.setSize(K,J,!1))},this.getSize=function(C){return C.set(K,J)},this.setSize=function(C,$,se=!0){if(xe.isPresenting){$e("WebGLRenderer: Can't change size while VR device is presenting.");return}K=C,J=$,t.width=Math.floor(C*j),t.height=Math.floor($*j),se===!0&&(t.style.width=C+"px",t.style.height=$+"px"),w!==null&&w.setSize(t.width,t.height),this.setViewport(0,0,C,$)},this.getDrawingBufferSize=function(C){return C.set(K*j,J*j).floor()},this.setDrawingBufferSize=function(C,$,se){K=C,J=$,j=se,t.width=Math.floor(C*se),t.height=Math.floor($*se),this.setViewport(0,0,C,$)},this.setEffects=function(C){if(g===Yt){ft("THREE.WebGLRenderer: setEffects() requires outputBufferType set to HalfFloatType or FloatType.");return}if(C){for(let $=0;$<C.length;$++)if(C[$].isOutputPass===!0){$e("THREE.WebGLRenderer: OutputPass is not needed in setEffects(). Tone mapping and color space conversion are applied automatically.");break}}w.setEffects(C||[])},this.getCurrentViewport=function(C){return C.copy(q)},this.getViewport=function(C){return C.copy(Z)},this.setViewport=function(C,$,se,te){C.isVector4?Z.set(C.x,C.y,C.z,C.w):Z.set(C,$,se,te),ce.viewport(q.copy(Z).multiplyScalar(j).round())},this.getScissor=function(C){return C.copy(fe)},this.setScissor=function(C,$,se,te){C.isVector4?fe.set(C.x,C.y,C.z,C.w):fe.set(C,$,se,te),ce.scissor(z.copy(fe).multiplyScalar(j).round())},this.getScissorTest=function(){return _e},this.setScissorTest=function(C){ce.setScissorTest(_e=C)},this.setOpaqueSort=function(C){V=C},this.setTransparentSort=function(C){Y=C},this.getClearColor=function(C){return C.copy(Se.getClearColor())},this.setClearColor=function(){Se.setClearColor(...arguments)},this.getClearAlpha=function(){return Se.getClearAlpha()},this.setClearAlpha=function(){Se.setClearAlpha(...arguments)},this.clear=function(C=!0,$=!0,se=!0){let te=0;if(C){let ne=!1;if(I!==null){const Le=I.texture.format;ne=p.has(Le)}if(ne){const Le=I.texture.type,He=_.has(Le),Ue=Se.getClearColor(),Xe=Se.getClearAlpha(),qe=Ue.r,et=Ue.g,tt=Ue.b;He?(M[0]=qe,M[1]=et,M[2]=tt,M[3]=Xe,B.clearBufferuiv(B.COLOR,0,M)):(y[0]=qe,y[1]=et,y[2]=tt,y[3]=Xe,B.clearBufferiv(B.COLOR,0,y))}else te|=B.COLOR_BUFFER_BIT}$&&(te|=B.DEPTH_BUFFER_BIT,this.state.buffers.depth.setMask(!0)),se&&(te|=B.STENCIL_BUFFER_BIT,this.state.buffers.stencil.setMask(4294967295)),te!==0&&B.clear(te)},this.clearColor=function(){this.clear(!0,!1,!1)},this.clearDepth=function(){this.clear(!1,!0,!1)},this.clearStencil=function(){this.clear(!1,!1,!0)},this.setNodesHandler=function(C){C.setRenderer(this),A=C},this.dispose=function(){t.removeEventListener("webglcontextlost",ae,!1),t.removeEventListener("webglcontextrestored",Pe,!1),t.removeEventListener("webglcontextcreationerror",Ke,!1),Se.dispose(),re.dispose(),he.dispose(),D.dispose(),H.dispose(),me.dispose(),pe.dispose(),ie.dispose(),Me.dispose(),xe.dispose(),xe.removeEventListener("sessionstart",pi),xe.removeEventListener("sessionend",qn),Lt.stop()};function ae(C){C.preventDefault(),cl("WebGLRenderer: Context Lost."),L=!0}function Pe(){cl("WebGLRenderer: Context Restored."),L=!1;const C=Te.autoReset,$=ve.enabled,se=ve.autoUpdate,te=ve.needsUpdate,ne=ve.type;we(),Te.autoReset=C,ve.enabled=$,ve.autoUpdate=se,ve.needsUpdate=te,ve.type=ne}function Ke(C){ft("WebGLRenderer: A WebGL context could not be created. Reason: ",C.statusMessage)}function st(C){const $=C.target;$.removeEventListener("dispose",st),Qe($)}function Qe(C){Ht(C),D.remove(C)}function Ht(C){const $=D.get(C).programs;$!==void 0&&($.forEach(function(se){Me.releaseProgram(se)}),C.isShaderMaterial&&Me.releaseShaderCache(C))}this.renderBufferDirect=function(C,$,se,te,ne,Le){$===null&&($=ze);const He=ne.isMesh&&ne.matrixWorld.determinant()<0,Ue=rs(C,$,se,te,ne);ce.setMaterial(te,He);let Xe=se.index,qe=1;if(te.wireframe===!0){if(Xe=oe.getWireframeAttribute(se),Xe===void 0)return;qe=2}const et=se.drawRange,tt=se.attributes.position;let je=et.start*qe,ct=(et.start+et.count)*qe;Le!==null&&(je=Math.max(je,Le.start*qe),ct=Math.min(ct,(Le.start+Le.count)*qe)),Xe!==null?(je=Math.max(je,0),ct=Math.min(ct,Xe.count)):tt!=null&&(je=Math.max(je,0),ct=Math.min(ct,tt.count));const Rt=ct-je;if(Rt<0||Rt===1/0)return;pe.setup(ne,te,Ue,se,Xe);let wt,mt=Ce;if(Xe!==null&&(wt=Q.get(Xe),mt=Ye,mt.setIndex(wt)),ne.isMesh)te.wireframe===!0?(ce.setLineWidth(te.wireframeLinewidth*ke()),mt.setMode(B.LINES)):mt.setMode(B.TRIANGLES);else if(ne.isLine){let yt=te.linewidth;yt===void 0&&(yt=1),ce.setLineWidth(yt*ke()),ne.isLineSegments?mt.setMode(B.LINES):ne.isLineLoop?mt.setMode(B.LINE_LOOP):mt.setMode(B.LINE_STRIP)}else ne.isPoints?mt.setMode(B.POINTS):ne.isSprite&&mt.setMode(B.TRIANGLES);if(ne.isBatchedMesh)if(De.get("WEBGL_multi_draw"))mt.renderMultiDraw(ne._multiDrawStarts,ne._multiDrawCounts,ne._multiDrawCount);else{const yt=ne._multiDrawStarts,Ve=ne._multiDrawCounts,tn=ne._multiDrawCount,rt=Xe?Q.get(Xe).bytesPerElement:1,_n=D.get(te).currentProgram.getUniforms();for(let vn=0;vn<tn;vn++)_n.setValue(B,"_gl_DrawID",vn),mt.render(yt[vn]/rt,Ve[vn])}else if(ne.isInstancedMesh)mt.renderInstances(je,Rt,ne.count);else if(se.isInstancedBufferGeometry){const yt=se._maxInstanceCount!==void 0?se._maxInstanceCount:1/0,Ve=Math.min(se.instanceCount,yt);mt.renderInstances(je,Rt,Ve)}else mt.render(je,Rt)};function jt(C,$,se){C.transparent===!0&&C.side===wn&&C.forceSinglePass===!1?(C.side=sn,C.needsUpdate=!0,Li(C,$,se),C.side=Xi,C.needsUpdate=!0,Li(C,$,se),C.side=wn):Li(C,$,se)}this.compile=function(C,$,se=null){se===null&&(se=C),b=he.get(se),b.init($),x.push(b),se.traverseVisible(function(ne){ne.isLight&&ne.layers.test($.layers)&&(b.pushLight(ne),ne.castShadow&&b.pushShadow(ne))}),C!==se&&C.traverseVisible(function(ne){ne.isLight&&ne.layers.test($.layers)&&(b.pushLight(ne),ne.castShadow&&b.pushShadow(ne))}),b.setupLights();const te=new Set;return C.traverse(function(ne){if(!(ne.isMesh||ne.isPoints||ne.isLine||ne.isSprite))return;const Le=ne.material;if(Le)if(Array.isArray(Le))for(let He=0;He<Le.length;He++){const Ue=Le[He];jt(Ue,se,ne),te.add(Ue)}else jt(Le,se,ne),te.add(Le)}),b=x.pop(),te},this.compileAsync=function(C,$,se=null){const te=this.compile(C,$,se);return new Promise(ne=>{function Le(){if(te.forEach(function(He){D.get(He).currentProgram.isReady()&&te.delete(He)}),te.size===0){ne(C);return}setTimeout(Le,10)}De.get("KHR_parallel_shader_compile")!==null?Le():setTimeout(Le,10)})};let Ln=null;function di(C){Ln&&Ln(C)}function pi(){Lt.stop()}function qn(){Lt.start()}const Lt=new Gm;Lt.setAnimationLoop(di),typeof self<"u"&&Lt.setContext(self),this.setAnimationLoop=function(C){Ln=C,xe.setAnimationLoop(C),C===null?Lt.stop():Lt.start()},xe.addEventListener("sessionstart",pi),xe.addEventListener("sessionend",qn),this.render=function(C,$){if($!==void 0&&$.isCamera!==!0){ft("WebGLRenderer.render: camera is not an instance of THREE.Camera.");return}if(L===!0)return;A!==null&&A.renderStart(C,$);const se=xe.enabled===!0&&xe.isPresenting===!0,te=w!==null&&(I===null||se)&&w.begin(R,I);if(C.matrixWorldAutoUpdate===!0&&C.updateMatrixWorld(),$.parent===null&&$.matrixWorldAutoUpdate===!0&&$.updateMatrixWorld(),xe.enabled===!0&&xe.isPresenting===!0&&(w===null||w.isCompositing()===!1)&&(xe.cameraAutoUpdate===!0&&xe.updateCamera($),$=xe.getCamera()),C.isScene===!0&&C.onBeforeRender(R,C,$,I),b=he.get(C,x.length),b.init($),b.state.textureUnits=T.getTextureUnits(),x.push(b),Ne.multiplyMatrices($.projectionMatrix,$.matrixWorldInverse),le.setFromProjectionMatrix(Ne,Ai,$.reversedDepth),Fe=this.localClippingEnabled,de=Re.init(this.clippingPlanes,Fe),S=re.get(C,E.length),S.init(),E.push(S),xe.enabled===!0&&xe.isPresenting===!0){const He=R.xr.getDepthSensingMesh();He!==null&&ei(He,$,-1/0,R.sortObjects)}ei(C,$,0,R.sortObjects),S.finish(),R.sortObjects===!0&&S.sort(V,Y),ge=xe.enabled===!1||xe.isPresenting===!1||xe.hasDepthSensing()===!1,ge&&Se.addToRenderList(S,C),this.info.render.frame++,de===!0&&Re.beginShadows();const ne=b.state.shadowsArray;if(ve.render(ne,C,$),de===!0&&Re.endShadows(),this.info.autoReset===!0&&this.info.reset(),(te&&w.hasRenderPass())===!1){const He=S.opaque,Ue=S.transmissive;if(b.setupLights(),$.isArrayCamera){const Xe=$.cameras;if(Ue.length>0)for(let qe=0,et=Xe.length;qe<et;qe++){const tt=Xe[qe];ts(He,Ue,C,tt)}ge&&Se.render(C);for(let qe=0,et=Xe.length;qe<et;qe++){const tt=Xe[qe];ea(S,C,tt,tt.viewport)}}else Ue.length>0&&ts(He,Ue,C,$),ge&&Se.render(C),ea(S,C,$)}I!==null&&P===0&&(T.updateMultisampleRenderTarget(I),T.updateRenderTargetMipmap(I)),te&&w.end(R),C.isScene===!0&&C.onAfterRender(R,C,$),pe.resetDefaultState(),F=-1,O=null,x.pop(),x.length>0?(b=x[x.length-1],T.setTextureUnits(b.state.textureUnits),de===!0&&Re.setGlobalState(R.clippingPlanes,b.state.camera)):b=null,E.pop(),E.length>0?S=E[E.length-1]:S=null,A!==null&&A.renderEnd()};function ei(C,$,se,te){if(C.visible===!1)return;if(C.layers.test($.layers)){if(C.isGroup)se=C.renderOrder;else if(C.isLOD)C.autoUpdate===!0&&C.update($);else if(C.isLightProbeGrid)b.pushLightProbeGrid(C);else if(C.isLight)b.pushLight(C),C.castShadow&&b.pushShadow(C);else if(C.isSprite){if(!C.frustumCulled||le.intersectsSprite(C)){te&&be.setFromMatrixPosition(C.matrixWorld).applyMatrix4(Ne);const He=me.update(C),Ue=C.material;Ue.visible&&S.push(C,He,Ue,se,be.z,null)}}else if((C.isMesh||C.isLine||C.isPoints)&&(!C.frustumCulled||le.intersectsObject(C))){const He=me.update(C),Ue=C.material;if(te&&(C.boundingSphere!==void 0?(C.boundingSphere===null&&C.computeBoundingSphere(),be.copy(C.boundingSphere.center)):(He.boundingSphere===null&&He.computeBoundingSphere(),be.copy(He.boundingSphere.center)),be.applyMatrix4(C.matrixWorld).applyMatrix4(Ne)),Array.isArray(Ue)){const Xe=He.groups;for(let qe=0,et=Xe.length;qe<et;qe++){const tt=Xe[qe],je=Ue[tt.materialIndex];je&&je.visible&&S.push(C,He,je,se,be.z,tt)}}else Ue.visible&&S.push(C,He,Ue,se,be.z,null)}}const Le=C.children;for(let He=0,Ue=Le.length;He<Ue;He++)ei(Le[He],$,se,te)}function ea(C,$,se,te){const{opaque:ne,transmissive:Le,transparent:He}=C;b.setupLightsView(se),de===!0&&Re.setGlobalState(R.clippingPlanes,se),te&&ce.viewport(q.copy(te)),ne.length>0&&ns(ne,$,se),Le.length>0&&ns(Le,$,se),He.length>0&&ns(He,$,se),ce.buffers.depth.setTest(!0),ce.buffers.depth.setMask(!0),ce.buffers.color.setMask(!0),ce.setPolygonOffset(!1)}function ts(C,$,se,te){if((se.isScene===!0?se.overrideMaterial:null)!==null)return;if(b.state.transmissionRenderTarget[te.id]===void 0){const je=De.has("EXT_color_buffer_half_float")||De.has("EXT_color_buffer_float");b.state.transmissionRenderTarget[te.id]=new $t(1,1,{generateMipmaps:!0,type:je?Yi:Yt,minFilter:Br,samples:Math.max(4,ye.samples),stencilBuffer:s,resolveDepthBuffer:!1,resolveStencilBuffer:!1,colorSpace:ut.workingColorSpace})}const Le=b.state.transmissionRenderTarget[te.id],He=te.viewport||q;Le.setSize(He.z*R.transmissionResolutionScale,He.w*R.transmissionResolutionScale);const Ue=R.getRenderTarget(),Xe=R.getActiveCubeFace(),qe=R.getActiveMipmapLevel();R.setRenderTarget(Le),R.getClearColor(N),G=R.getClearAlpha(),G<1&&R.setClearColor(16777215,.5),R.clear(),ge&&Se.render(se);const et=R.toneMapping;R.toneMapping=Pi;const tt=te.viewport;if(te.viewport!==void 0&&(te.viewport=void 0),b.setupLightsView(te),de===!0&&Re.setGlobalState(R.clippingPlanes,te),ns(C,se,te),T.updateMultisampleRenderTarget(Le),T.updateRenderTargetMipmap(Le),De.has("WEBGL_multisampled_render_to_texture")===!1){let je=!1;for(let ct=0,Rt=$.length;ct<Rt;ct++){const wt=$[ct],{object:mt,geometry:yt,material:Ve,group:tn}=wt;if(Ve.side===wn&&mt.layers.test(te.layers)){const rt=Ve.side;Ve.side=sn,Ve.needsUpdate=!0,ta(mt,se,te,yt,Ve,tn),Ve.side=rt,Ve.needsUpdate=!0,je=!0}}je===!0&&(T.updateMultisampleRenderTarget(Le),T.updateRenderTargetMipmap(Le))}R.setRenderTarget(Ue,Xe,qe),R.setClearColor(N,G),tt!==void 0&&(te.viewport=tt),R.toneMapping=et}function ns(C,$,se){const te=$.isScene===!0?$.overrideMaterial:null;for(let ne=0,Le=C.length;ne<Le;ne++){const He=C[ne],{object:Ue,geometry:Xe,group:qe}=He;let et=He.material;et.allowOverride===!0&&te!==null&&(et=te),Ue.layers.test(se.layers)&&ta(Ue,$,se,Xe,et,qe)}}function ta(C,$,se,te,ne,Le){C.onBeforeRender(R,$,se,te,ne,Le),C.modelViewMatrix.multiplyMatrices(se.matrixWorldInverse,C.matrixWorld),C.normalMatrix.getNormalMatrix(C.modelViewMatrix),ne.onBeforeRender(R,$,se,te,C,Le),ne.transparent===!0&&ne.side===wn&&ne.forceSinglePass===!1?(ne.side=sn,ne.needsUpdate=!0,R.renderBufferDirect(se,$,te,ne,C,Le),ne.side=Xi,ne.needsUpdate=!0,R.renderBufferDirect(se,$,te,ne,C,Le),ne.side=wn):R.renderBufferDirect(se,$,te,ne,C,Le),C.onAfterRender(R,$,se,te,ne,Le)}function Li(C,$,se){$.isScene!==!0&&($=ze);const te=D.get(C),ne=b.state.lights,Le=b.state.shadowsArray,He=ne.state.version,Ue=Me.getParameters(C,ne.state,Le,$,se,b.state.lightProbeGridArray),Xe=Me.getProgramCacheKey(Ue);let qe=te.programs;te.environment=C.isMeshStandardMaterial||C.isMeshLambertMaterial||C.isMeshPhongMaterial?$.environment:null,te.fog=$.fog;const et=C.isMeshStandardMaterial||C.isMeshLambertMaterial&&!C.envMap||C.isMeshPhongMaterial&&!C.envMap;te.envMap=H.get(C.envMap||te.environment,et),te.envMapRotation=te.environment!==null&&C.envMap===null?$.environmentRotation:C.envMapRotation,qe===void 0&&(C.addEventListener("dispose",st),qe=new Map,te.programs=qe);let tt=qe.get(Xe);if(tt!==void 0){if(te.currentProgram===tt&&te.lightsStateVersion===He)return eo(C,Ue),tt}else Ue.uniforms=Me.getUniforms(C),A!==null&&C.isNodeMaterial&&A.build(C,se,Ue),C.onBeforeCompile(Ue,R),tt=Me.acquireProgram(Ue,Xe),qe.set(Xe,tt),te.uniforms=Ue.uniforms;const je=te.uniforms;return(!C.isShaderMaterial&&!C.isRawShaderMaterial||C.clipping===!0)&&(je.clippingPlanes=Re.uniform),eo(C,Ue),te.needsLights=ia(C),te.lightsStateVersion=He,te.needsLights&&(je.ambientLightColor.value=ne.state.ambient,je.lightProbe.value=ne.state.probe,je.directionalLights.value=ne.state.directional,je.directionalLightShadows.value=ne.state.directionalShadow,je.spotLights.value=ne.state.spot,je.spotLightShadows.value=ne.state.spotShadow,je.rectAreaLights.value=ne.state.rectArea,je.ltc_1.value=ne.state.rectAreaLTC1,je.ltc_2.value=ne.state.rectAreaLTC2,je.pointLights.value=ne.state.point,je.pointLightShadows.value=ne.state.pointShadow,je.hemisphereLights.value=ne.state.hemi,je.directionalShadowMatrix.value=ne.state.directionalShadowMatrix,je.spotLightMatrix.value=ne.state.spotLightMatrix,je.spotLightMap.value=ne.state.spotLightMap,je.pointShadowMatrix.value=ne.state.pointShadowMatrix),te.lightProbeGrid=b.state.lightProbeGridArray.length>0,te.currentProgram=tt,te.uniformsList=null,tt}function is(C){if(C.uniformsList===null){const $=C.currentProgram.getUniforms();C.uniformsList=Zo.seqWithValue($.seq,C.uniforms)}return C.uniformsList}function eo(C,$){const se=D.get(C);se.outputColorSpace=$.outputColorSpace,se.batching=$.batching,se.batchingColor=$.batchingColor,se.instancing=$.instancing,se.instancingColor=$.instancingColor,se.instancingMorph=$.instancingMorph,se.skinning=$.skinning,se.morphTargets=$.morphTargets,se.morphNormals=$.morphNormals,se.morphColors=$.morphColors,se.morphTargetsCount=$.morphTargetsCount,se.numClippingPlanes=$.numClippingPlanes,se.numIntersection=$.numClipIntersection,se.vertexAlphas=$.vertexAlphas,se.vertexTangents=$.vertexTangents,se.toneMapping=$.toneMapping}function to(C,$){if(C.length===0)return null;if(C.length===1)return C[0].texture!==null?C[0]:null;v.setFromMatrixPosition($.matrixWorld);for(let se=0,te=C.length;se<te;se++){const ne=C[se];if(ne.texture!==null&&ne.boundingBox.containsPoint(v))return ne}return null}function rs(C,$,se,te,ne){$.isScene!==!0&&($=ze),T.resetTextureUnits();const Le=$.fog,He=te.isMeshStandardMaterial||te.isMeshLambertMaterial||te.isMeshPhongMaterial?$.environment:null,Ue=I===null?R.outputColorSpace:I.isXRRenderTarget===!0?I.texture.colorSpace:ut.workingColorSpace,Xe=te.isMeshStandardMaterial||te.isMeshLambertMaterial&&!te.envMap||te.isMeshPhongMaterial&&!te.envMap,qe=H.get(te.envMap||He,Xe),et=te.vertexColors===!0&&!!se.attributes.color&&se.attributes.color.itemSize===4,tt=!!se.attributes.tangent&&(!!te.normalMap||te.anisotropy>0),je=!!se.morphAttributes.position,ct=!!se.morphAttributes.normal,Rt=!!se.morphAttributes.color;let wt=Pi;te.toneMapped&&(I===null||I.isXRRenderTarget===!0)&&(wt=R.toneMapping);const mt=se.morphAttributes.position||se.morphAttributes.normal||se.morphAttributes.color,yt=mt!==void 0?mt.length:0,Ve=D.get(te),tn=b.state.lights;if(de===!0&&(Fe===!0||C!==O)){const dt=C===O&&te.id===F;Re.setState(te,C,dt)}let rt=!1;te.version===Ve.__version?(Ve.needsLights&&Ve.lightsStateVersion!==tn.state.version||Ve.outputColorSpace!==Ue||ne.isBatchedMesh&&Ve.batching===!1||!ne.isBatchedMesh&&Ve.batching===!0||ne.isBatchedMesh&&Ve.batchingColor===!0&&ne.colorTexture===null||ne.isBatchedMesh&&Ve.batchingColor===!1&&ne.colorTexture!==null||ne.isInstancedMesh&&Ve.instancing===!1||!ne.isInstancedMesh&&Ve.instancing===!0||ne.isSkinnedMesh&&Ve.skinning===!1||!ne.isSkinnedMesh&&Ve.skinning===!0||ne.isInstancedMesh&&Ve.instancingColor===!0&&ne.instanceColor===null||ne.isInstancedMesh&&Ve.instancingColor===!1&&ne.instanceColor!==null||ne.isInstancedMesh&&Ve.instancingMorph===!0&&ne.morphTexture===null||ne.isInstancedMesh&&Ve.instancingMorph===!1&&ne.morphTexture!==null||Ve.envMap!==qe||te.fog===!0&&Ve.fog!==Le||Ve.numClippingPlanes!==void 0&&(Ve.numClippingPlanes!==Re.numPlanes||Ve.numIntersection!==Re.numIntersection)||Ve.vertexAlphas!==et||Ve.vertexTangents!==tt||Ve.morphTargets!==je||Ve.morphNormals!==ct||Ve.morphColors!==Rt||Ve.toneMapping!==wt||Ve.morphTargetsCount!==yt||!!Ve.lightProbeGrid!=b.state.lightProbeGridArray.length>0)&&(rt=!0):(rt=!0,Ve.__version=te.version);let _n=Ve.currentProgram;rt===!0&&(_n=Li(te,$,ne),A&&te.isNodeMaterial&&A.onUpdateProgram(te,_n,Ve));let vn=!1,In=!1,mi=!1;const _t=_n.getUniforms(),Pt=Ve.uniforms;if(ce.useProgram(_n.program)&&(vn=!0,In=!0,mi=!0),te.id!==F&&(F=te.id,In=!0),Ve.needsLights){const dt=to(b.state.lightProbeGridArray,ne);Ve.lightProbeGrid!==dt&&(Ve.lightProbeGrid=dt,In=!0)}if(vn||O!==C){ce.buffers.depth.getReversed()&&C.reversedDepth!==!0&&(C._reversedDepth=!0,C.updateProjectionMatrix()),_t.setValue(B,"projectionMatrix",C.projectionMatrix),_t.setValue(B,"viewMatrix",C.matrixWorldInverse);const ti=_t.map.cameraPosition;ti!==void 0&&ti.setValue(B,Ae.setFromMatrixPosition(C.matrixWorld)),ye.logarithmicDepthBuffer&&_t.setValue(B,"logDepthBufFC",2/(Math.log(C.far+1)/Math.LN2)),(te.isMeshPhongMaterial||te.isMeshToonMaterial||te.isMeshLambertMaterial||te.isMeshBasicMaterial||te.isMeshStandardMaterial||te.isShaderMaterial)&&_t.setValue(B,"isOrthographic",C.isOrthographicCamera===!0),O!==C&&(O=C,In=!0,mi=!0)}if(Ve.needsLights&&(tn.state.directionalShadowMap.length>0&&_t.setValue(B,"directionalShadowMap",tn.state.directionalShadowMap,T),tn.state.spotShadowMap.length>0&&_t.setValue(B,"spotShadowMap",tn.state.spotShadowMap,T),tn.state.pointShadowMap.length>0&&_t.setValue(B,"pointShadowMap",tn.state.pointShadowMap,T)),ne.isSkinnedMesh){_t.setOptional(B,ne,"bindMatrix"),_t.setOptional(B,ne,"bindMatrixInverse");const dt=ne.skeleton;dt&&(dt.boneTexture===null&&dt.computeBoneTexture(),_t.setValue(B,"boneTexture",dt.boneTexture,T))}ne.isBatchedMesh&&(_t.setOptional(B,ne,"batchingTexture"),_t.setValue(B,"batchingTexture",ne._matricesTexture,T),_t.setOptional(B,ne,"batchingIdTexture"),_t.setValue(B,"batchingIdTexture",ne._indirectTexture,T),_t.setOptional(B,ne,"batchingColorTexture"),ne._colorsTexture!==null&&_t.setValue(B,"batchingColorTexture",ne._colorsTexture,T));const jn=se.morphAttributes;if((jn.position!==void 0||jn.normal!==void 0||jn.color!==void 0)&&Ge.update(ne,se,_n),(In||Ve.receiveShadow!==ne.receiveShadow)&&(Ve.receiveShadow=ne.receiveShadow,_t.setValue(B,"receiveShadow",ne.receiveShadow)),(te.isMeshStandardMaterial||te.isMeshLambertMaterial||te.isMeshPhongMaterial)&&te.envMap===null&&$.environment!==null&&(Pt.envMapIntensity.value=$.environmentIntensity),Pt.dfgLUT!==void 0&&(Pt.dfgLUT.value=ib()),In){if(_t.setValue(B,"toneMappingExposure",R.toneMappingExposure),Ve.needsLights&&na(Pt,mi),Le&&te.fog===!0&&ee.refreshFogUniforms(Pt,Le),ee.refreshMaterialUniforms(Pt,te,j,J,b.state.transmissionRenderTarget[C.id]),Ve.needsLights&&Ve.lightProbeGrid){const dt=Ve.lightProbeGrid;Pt.probesSH.value=dt.texture,Pt.probesMin.value.copy(dt.boundingBox.min),Pt.probesMax.value.copy(dt.boundingBox.max),Pt.probesResolution.value.copy(dt.resolution)}Zo.upload(B,is(Ve),Pt,T)}if(te.isShaderMaterial&&te.uniformsNeedUpdate===!0&&(Zo.upload(B,is(Ve),Pt,T),te.uniformsNeedUpdate=!1),te.isSpriteMaterial&&_t.setValue(B,"center",ne.center),_t.setValue(B,"modelViewMatrix",ne.modelViewMatrix),_t.setValue(B,"normalMatrix",ne.normalMatrix),_t.setValue(B,"modelMatrix",ne.matrixWorld),te.uniformsGroups!==void 0){const dt=te.uniformsGroups;for(let ti=0,ni=dt.length;ti<ni;ti++){const Ii=dt[ti];ie.update(Ii,_n),ie.bind(Ii,_n)}}return _n}function na(C,$){C.ambientLightColor.needsUpdate=$,C.lightProbe.needsUpdate=$,C.directionalLights.needsUpdate=$,C.directionalLightShadows.needsUpdate=$,C.pointLights.needsUpdate=$,C.pointLightShadows.needsUpdate=$,C.spotLights.needsUpdate=$,C.spotLightShadows.needsUpdate=$,C.rectAreaLights.needsUpdate=$,C.hemisphereLights.needsUpdate=$}function ia(C){return C.isMeshLambertMaterial||C.isMeshToonMaterial||C.isMeshPhongMaterial||C.isMeshStandardMaterial||C.isShadowMaterial||C.isShaderMaterial&&C.lights===!0}this.getActiveCubeFace=function(){return U},this.getActiveMipmapLevel=function(){return P},this.getRenderTarget=function(){return I},this.setRenderTargetTextures=function(C,$,se){const te=D.get(C);te.__autoAllocateDepthBuffer=C.resolveDepthBuffer===!1,te.__autoAllocateDepthBuffer===!1&&(te.__useRenderToTexture=!1),D.get(C.texture).__webglTexture=$,D.get(C.depthTexture).__webglTexture=te.__autoAllocateDepthBuffer?void 0:se,te.__hasExternalTextures=!0},this.setRenderTargetFramebuffer=function(C,$){const se=D.get(C);se.__webglFramebuffer=$,se.__useDefaultFramebuffer=$===void 0};const Ze=B.createFramebuffer();this.setRenderTarget=function(C,$=0,se=0){I=C,U=$,P=se;let te=null,ne=!1,Le=!1;if(C){const Ue=D.get(C);if(Ue.__useDefaultFramebuffer!==void 0){ce.bindFramebuffer(B.FRAMEBUFFER,Ue.__webglFramebuffer),q.copy(C.viewport),z.copy(C.scissor),k=C.scissorTest,ce.viewport(q),ce.scissor(z),ce.setScissorTest(k),F=-1;return}else if(Ue.__webglFramebuffer===void 0)T.setupRenderTarget(C);else if(Ue.__hasExternalTextures)T.rebindTextures(C,D.get(C.texture).__webglTexture,D.get(C.depthTexture).__webglTexture);else if(C.depthBuffer){const et=C.depthTexture;if(Ue.__boundDepthTexture!==et){if(et!==null&&D.has(et)&&(C.width!==et.image.width||C.height!==et.image.height))throw new Error("WebGLRenderTarget: Attached DepthTexture is initialized to the incorrect size.");T.setupDepthRenderbuffer(C)}}const Xe=C.texture;(Xe.isData3DTexture||Xe.isDataArrayTexture||Xe.isCompressedArrayTexture)&&(Le=!0);const qe=D.get(C).__webglFramebuffer;C.isWebGLCubeRenderTarget?(Array.isArray(qe[$])?te=qe[$][se]:te=qe[$],ne=!0):C.samples>0&&T.useMultisampledRTT(C)===!1?te=D.get(C).__webglMultisampledFramebuffer:Array.isArray(qe)?te=qe[se]:te=qe,q.copy(C.viewport),z.copy(C.scissor),k=C.scissorTest}else q.copy(Z).multiplyScalar(j).floor(),z.copy(fe).multiplyScalar(j).floor(),k=_e;if(se!==0&&(te=Ze),ce.bindFramebuffer(B.FRAMEBUFFER,te)&&ce.drawBuffers(C,te),ce.viewport(q),ce.scissor(z),ce.setScissorTest(k),ne){const Ue=D.get(C.texture);B.framebufferTexture2D(B.FRAMEBUFFER,B.COLOR_ATTACHMENT0,B.TEXTURE_CUBE_MAP_POSITIVE_X+$,Ue.__webglTexture,se)}else if(Le){const Ue=$;for(let Xe=0;Xe<C.textures.length;Xe++){const qe=D.get(C.textures[Xe]);B.framebufferTextureLayer(B.FRAMEBUFFER,B.COLOR_ATTACHMENT0+Xe,qe.__webglTexture,se,Ue)}}else if(C!==null&&se!==0){const Ue=D.get(C.texture);B.framebufferTexture2D(B.FRAMEBUFFER,B.COLOR_ATTACHMENT0,B.TEXTURE_2D,Ue.__webglTexture,se)}F=-1},this.readRenderTargetPixels=function(C,$,se,te,ne,Le,He,Ue=0){if(!(C&&C.isWebGLRenderTarget)){ft("WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");return}let Xe=D.get(C).__webglFramebuffer;if(C.isWebGLCubeRenderTarget&&He!==void 0&&(Xe=Xe[He]),Xe){ce.bindFramebuffer(B.FRAMEBUFFER,Xe);try{const qe=C.textures[Ue],et=qe.format,tt=qe.type;if(C.textures.length>1&&B.readBuffer(B.COLOR_ATTACHMENT0+Ue),!ye.textureFormatReadable(et)){ft("WebGLRenderer.readRenderTargetPixels: renderTarget is not in RGBA or implementation defined format.");return}if(!ye.textureTypeReadable(tt)){ft("WebGLRenderer.readRenderTargetPixels: renderTarget is not in UnsignedByteType or implementation defined type.");return}$>=0&&$<=C.width-te&&se>=0&&se<=C.height-ne&&B.readPixels($,se,te,ne,W.convert(et),W.convert(tt),Le)}finally{const qe=I!==null?D.get(I).__webglFramebuffer:null;ce.bindFramebuffer(B.FRAMEBUFFER,qe)}}},this.readRenderTargetPixelsAsync=async function(C,$,se,te,ne,Le,He,Ue=0){if(!(C&&C.isWebGLRenderTarget))throw new Error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");let Xe=D.get(C).__webglFramebuffer;if(C.isWebGLCubeRenderTarget&&He!==void 0&&(Xe=Xe[He]),Xe)if($>=0&&$<=C.width-te&&se>=0&&se<=C.height-ne){ce.bindFramebuffer(B.FRAMEBUFFER,Xe);const qe=C.textures[Ue],et=qe.format,tt=qe.type;if(C.textures.length>1&&B.readBuffer(B.COLOR_ATTACHMENT0+Ue),!ye.textureFormatReadable(et))throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in RGBA or implementation defined format.");if(!ye.textureTypeReadable(tt))throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in UnsignedByteType or implementation defined type.");const je=B.createBuffer();B.bindBuffer(B.PIXEL_PACK_BUFFER,je),B.bufferData(B.PIXEL_PACK_BUFFER,Le.byteLength,B.STREAM_READ),B.readPixels($,se,te,ne,W.convert(et),W.convert(tt),0);const ct=I!==null?D.get(I).__webglFramebuffer:null;ce.bindFramebuffer(B.FRAMEBUFFER,ct);const Rt=B.fenceSync(B.SYNC_GPU_COMMANDS_COMPLETE,0);return B.flush(),await b_(B,Rt,4),B.bindBuffer(B.PIXEL_PACK_BUFFER,je),B.getBufferSubData(B.PIXEL_PACK_BUFFER,0,Le),B.deleteBuffer(je),B.deleteSync(Rt),Le}else throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: requested read bounds are out of range.")},this.copyFramebufferToTexture=function(C,$=null,se=0){const te=Math.pow(2,-se),ne=Math.floor(C.image.width*te),Le=Math.floor(C.image.height*te),He=$!==null?$.x:0,Ue=$!==null?$.y:0;T.setTexture2D(C,0),B.copyTexSubImage2D(B.TEXTURE_2D,se,0,0,He,Ue,ne,Le),ce.unbindTexture()};const Er=B.createFramebuffer(),Yl=B.createFramebuffer();this.copyTextureToTexture=function(C,$,se=null,te=null,ne=0,Le=0){let He,Ue,Xe,qe,et,tt,je,ct,Rt;const wt=C.isCompressedTexture?C.mipmaps[Le]:C.image;if(se!==null)He=se.max.x-se.min.x,Ue=se.max.y-se.min.y,Xe=se.isBox3?se.max.z-se.min.z:1,qe=se.min.x,et=se.min.y,tt=se.isBox3?se.min.z:0;else{const Pt=Math.pow(2,-ne);He=Math.floor(wt.width*Pt),Ue=Math.floor(wt.height*Pt),C.isDataArrayTexture?Xe=wt.depth:C.isData3DTexture?Xe=Math.floor(wt.depth*Pt):Xe=1,qe=0,et=0,tt=0}te!==null?(je=te.x,ct=te.y,Rt=te.z):(je=0,ct=0,Rt=0);const mt=W.convert($.format),yt=W.convert($.type);let Ve;$.isData3DTexture?(T.setTexture3D($,0),Ve=B.TEXTURE_3D):$.isDataArrayTexture||$.isCompressedArrayTexture?(T.setTexture2DArray($,0),Ve=B.TEXTURE_2D_ARRAY):(T.setTexture2D($,0),Ve=B.TEXTURE_2D),ce.activeTexture(B.TEXTURE0),ce.pixelStorei(B.UNPACK_FLIP_Y_WEBGL,$.flipY),ce.pixelStorei(B.UNPACK_PREMULTIPLY_ALPHA_WEBGL,$.premultiplyAlpha),ce.pixelStorei(B.UNPACK_ALIGNMENT,$.unpackAlignment);const tn=ce.getParameter(B.UNPACK_ROW_LENGTH),rt=ce.getParameter(B.UNPACK_IMAGE_HEIGHT),_n=ce.getParameter(B.UNPACK_SKIP_PIXELS),vn=ce.getParameter(B.UNPACK_SKIP_ROWS),In=ce.getParameter(B.UNPACK_SKIP_IMAGES);ce.pixelStorei(B.UNPACK_ROW_LENGTH,wt.width),ce.pixelStorei(B.UNPACK_IMAGE_HEIGHT,wt.height),ce.pixelStorei(B.UNPACK_SKIP_PIXELS,qe),ce.pixelStorei(B.UNPACK_SKIP_ROWS,et),ce.pixelStorei(B.UNPACK_SKIP_IMAGES,tt);const mi=C.isDataArrayTexture||C.isData3DTexture,_t=$.isDataArrayTexture||$.isData3DTexture;if(C.isDepthTexture){const Pt=D.get(C),jn=D.get($),dt=D.get(Pt.__renderTarget),ti=D.get(jn.__renderTarget);ce.bindFramebuffer(B.READ_FRAMEBUFFER,dt.__webglFramebuffer),ce.bindFramebuffer(B.DRAW_FRAMEBUFFER,ti.__webglFramebuffer);for(let ni=0;ni<Xe;ni++)mi&&(B.framebufferTextureLayer(B.READ_FRAMEBUFFER,B.COLOR_ATTACHMENT0,D.get(C).__webglTexture,ne,tt+ni),B.framebufferTextureLayer(B.DRAW_FRAMEBUFFER,B.COLOR_ATTACHMENT0,D.get($).__webglTexture,Le,Rt+ni)),B.blitFramebuffer(qe,et,He,Ue,je,ct,He,Ue,B.DEPTH_BUFFER_BIT,B.NEAREST);ce.bindFramebuffer(B.READ_FRAMEBUFFER,null),ce.bindFramebuffer(B.DRAW_FRAMEBUFFER,null)}else if(ne!==0||C.isRenderTargetTexture||D.has(C)){const Pt=D.get(C),jn=D.get($);ce.bindFramebuffer(B.READ_FRAMEBUFFER,Er),ce.bindFramebuffer(B.DRAW_FRAMEBUFFER,Yl);for(let dt=0;dt<Xe;dt++)mi?B.framebufferTextureLayer(B.READ_FRAMEBUFFER,B.COLOR_ATTACHMENT0,Pt.__webglTexture,ne,tt+dt):B.framebufferTexture2D(B.READ_FRAMEBUFFER,B.COLOR_ATTACHMENT0,B.TEXTURE_2D,Pt.__webglTexture,ne),_t?B.framebufferTextureLayer(B.DRAW_FRAMEBUFFER,B.COLOR_ATTACHMENT0,jn.__webglTexture,Le,Rt+dt):B.framebufferTexture2D(B.DRAW_FRAMEBUFFER,B.COLOR_ATTACHMENT0,B.TEXTURE_2D,jn.__webglTexture,Le),ne!==0?B.blitFramebuffer(qe,et,He,Ue,je,ct,He,Ue,B.COLOR_BUFFER_BIT,B.NEAREST):_t?B.copyTexSubImage3D(Ve,Le,je,ct,Rt+dt,qe,et,He,Ue):B.copyTexSubImage2D(Ve,Le,je,ct,qe,et,He,Ue);ce.bindFramebuffer(B.READ_FRAMEBUFFER,null),ce.bindFramebuffer(B.DRAW_FRAMEBUFFER,null)}else _t?C.isDataTexture||C.isData3DTexture?B.texSubImage3D(Ve,Le,je,ct,Rt,He,Ue,Xe,mt,yt,wt.data):$.isCompressedArrayTexture?B.compressedTexSubImage3D(Ve,Le,je,ct,Rt,He,Ue,Xe,mt,wt.data):B.texSubImage3D(Ve,Le,je,ct,Rt,He,Ue,Xe,mt,yt,wt):C.isDataTexture?B.texSubImage2D(B.TEXTURE_2D,Le,je,ct,He,Ue,mt,yt,wt.data):C.isCompressedTexture?B.compressedTexSubImage2D(B.TEXTURE_2D,Le,je,ct,wt.width,wt.height,mt,wt.data):B.texSubImage2D(B.TEXTURE_2D,Le,je,ct,He,Ue,mt,yt,wt);ce.pixelStorei(B.UNPACK_ROW_LENGTH,tn),ce.pixelStorei(B.UNPACK_IMAGE_HEIGHT,rt),ce.pixelStorei(B.UNPACK_SKIP_PIXELS,_n),ce.pixelStorei(B.UNPACK_SKIP_ROWS,vn),ce.pixelStorei(B.UNPACK_SKIP_IMAGES,In),Le===0&&$.generateMipmaps&&B.generateMipmap(Ve),ce.unbindTexture()},this.initRenderTarget=function(C){D.get(C).__webglFramebuffer===void 0&&T.setupRenderTarget(C)},this.initTexture=function(C){C.isCubeTexture?T.setTextureCube(C,0):C.isData3DTexture?T.setTexture3D(C,0):C.isDataArrayTexture||C.isCompressedArrayTexture?T.setTexture2DArray(C,0):T.setTexture2D(C,0),ce.unbindTexture()},this.resetState=function(){U=0,P=0,I=null,ce.reset(),pe.reset()},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}get coordinateSystem(){return Ai}get outputColorSpace(){return this._outputColorSpace}set outputColorSpace(e){this._outputColorSpace=e;const t=this.getContext();t.drawingBufferColorSpace=ut._getDrawingBufferColorSpace(e),t.unpackColorSpace=ut._getUnpackColorSpace()}}function sb(){var n=Object.create(null);function e(i,s){var a=i.id,o=i.name,l=i.dependencies;l===void 0&&(l=[]);var c=i.init;c===void 0&&(c=function(){});var u=i.getTransferables;if(u===void 0&&(u=null),!n[a])try{l=l.map(function(h){return h&&h.isWorkerModule&&(e(h,function(d){if(d instanceof Error)throw d}),h=n[h.id].value),h}),c=r("<"+o+">.init",c),u&&(u=r("<"+o+">.getTransferables",u));var f=null;typeof c=="function"?f=c.apply(void 0,l):console.error("worker module init function failed to rehydrate"),n[a]={id:a,value:f,getTransferables:u},s(f)}catch(h){h&&h.noLog||console.error(h),s(h)}}function t(i,s){var a,o=i.id,l=i.args;(!n[o]||typeof n[o].value!="function")&&s(new Error("Worker module "+o+": not found or its 'init' did not return a function"));try{var c=(a=n[o]).value.apply(a,l);c&&typeof c.then=="function"?c.then(u,function(f){return s(f instanceof Error?f:new Error(""+f))}):u(c)}catch(f){s(f)}function u(f){try{var h=n[o].getTransferables&&n[o].getTransferables(f);(!h||!Array.isArray(h)||!h.length)&&(h=void 0),s(f,h)}catch(d){console.error(d),s(d)}}}function r(i,s){var a=void 0;self.troikaDefine=function(l){return a=l};var o=URL.createObjectURL(new Blob(["/** "+i.replace(/\*/g,"")+` **/

troikaDefine(
`+s+`
)`],{type:"application/javascript"}));try{importScripts(o)}catch(l){console.error(l)}return URL.revokeObjectURL(o),delete self.troikaDefine,a}self.addEventListener("message",function(i){var s=i.data,a=s.messageId,o=s.action,l=s.data;try{o==="registerModule"&&e(l,function(c){c instanceof Error?postMessage({messageId:a,success:!1,error:c.message}):postMessage({messageId:a,success:!0,result:{isCallable:typeof c=="function"}})}),o==="callModule"&&t(l,function(c,u){c instanceof Error?postMessage({messageId:a,success:!1,error:c.message}):postMessage({messageId:a,success:!0,result:c},u||void 0)})}catch(c){postMessage({messageId:a,success:!1,error:c.stack})}})}function ab(n){var e=function(){for(var t=[],r=arguments.length;r--;)t[r]=arguments[r];return e._getInitResult().then(function(i){if(typeof i=="function")return i.apply(void 0,t);throw new Error("Worker module function was called but `init` did not return a callable function")})};return e._getInitResult=function(){var t=n.dependencies,r=n.init;t=Array.isArray(t)?t.map(function(s){return s&&(s=s.onMainThread||s,s._getInitResult&&(s=s._getInitResult())),s}):[];var i=Promise.all(t).then(function(s){return r.apply(null,s)});return e._getInitResult=function(){return i},i},e}var Km=function(){var n=!1;if(typeof window<"u"&&typeof window.document<"u")try{var e=new Worker(URL.createObjectURL(new Blob([""],{type:"application/javascript"})));e.terminate(),n=!0}catch(t){console.log("Troika createWorkerModule: web workers not allowed; falling back to main thread execution. Cause: ["+t.message+"]")}return Km=function(){return n},n},ob=0,lb=0,Nc=!1,Pa=Object.create(null),Da=Object.create(null),mh=Object.create(null);function Zs(n){if((!n||typeof n.init!="function")&&!Nc)throw new Error("requires `options.init` function");var e=n.dependencies,t=n.init,r=n.getTransferables,i=n.workerId,s=ab(n);i==null&&(i="#default");var a="workerModule"+ ++ob,o=n.name||a,l=null;e=e&&e.map(function(u){return typeof u=="function"&&!u.workerModuleData&&(Nc=!0,u=Zs({workerId:i,name:"<"+o+"> function dependency: "+u.name,init:`function(){return (
`+$o(u)+`
)}`}),Nc=!1),u&&u.workerModuleData&&(u=u.workerModuleData),u});function c(){for(var u=[],f=arguments.length;f--;)u[f]=arguments[f];if(!Km())return s.apply(void 0,u);if(!l){l=Qd(i,"registerModule",c.workerModuleData);var h=function(){l=null,Da[i].delete(h)};(Da[i]||(Da[i]=new Set)).add(h)}return l.then(function(d){var m=d.isCallable;if(m)return Qd(i,"callModule",{id:a,args:u});throw new Error("Worker module function was called but `init` did not return a callable function")})}return c.workerModuleData={isWorkerModule:!0,id:a,name:o,dependencies:e,init:$o(t),getTransferables:r&&$o(r)},c.onMainThread=s,c}function cb(n){Da[n]&&Da[n].forEach(function(e){e()}),Pa[n]&&(Pa[n].terminate(),delete Pa[n])}function $o(n){var e=n.toString();return!/^function/.test(e)&&/^\w+\s*\(/.test(e)&&(e="function "+e),e}function ub(n){var e=Pa[n];if(!e){var t=$o(sb);e=Pa[n]=new Worker(URL.createObjectURL(new Blob(["/** Worker Module Bootstrap: "+n.replace(/\*/g,"")+` **/

;(`+t+")()"],{type:"application/javascript"}))),e.onmessage=function(r){var i=r.data,s=i.messageId,a=mh[s];if(!a)throw new Error("WorkerModule response with empty or unknown messageId");delete mh[s],a(i)}}return e}function Qd(n,e,t){return new Promise(function(r,i){var s=++lb;mh[s]=function(a){a.success?r(a.result):i(new Error("Error in worker "+e+" call: "+a.error))},ub(n).postMessage({messageId:s,action:e,data:t})})}function Zm(){var n=(function(e){function t(z,k,N,G,K,J,j,V){var Y=1-j;V.x=Y*Y*z+2*Y*j*N+j*j*K,V.y=Y*Y*k+2*Y*j*G+j*j*J}function r(z,k,N,G,K,J,j,V,Y,Z){var fe=1-Y;Z.x=fe*fe*fe*z+3*fe*fe*Y*N+3*fe*Y*Y*K+Y*Y*Y*j,Z.y=fe*fe*fe*k+3*fe*fe*Y*G+3*fe*Y*Y*J+Y*Y*Y*V}function i(z,k){for(var N=/([MLQCZ])([^MLQCZ]*)/g,G,K,J,j,V;G=N.exec(z);){var Y=G[2].replace(/^\s*|\s*$/g,"").split(/[,\s]+/).map(function(Z){return parseFloat(Z)});switch(G[1]){case"M":j=K=Y[0],V=J=Y[1];break;case"L":(Y[0]!==j||Y[1]!==V)&&k("L",j,V,j=Y[0],V=Y[1]);break;case"Q":{k("Q",j,V,j=Y[2],V=Y[3],Y[0],Y[1]);break}case"C":{k("C",j,V,j=Y[4],V=Y[5],Y[0],Y[1],Y[2],Y[3]);break}case"Z":(j!==K||V!==J)&&k("L",j,V,K,J);break}}}function s(z,k,N){N===void 0&&(N=16);var G={x:0,y:0};i(z,function(K,J,j,V,Y,Z,fe,_e,le){switch(K){case"L":k(J,j,V,Y);break;case"Q":{for(var de=J,Fe=j,Ne=1;Ne<N;Ne++)t(J,j,Z,fe,V,Y,Ne/(N-1),G),k(de,Fe,G.x,G.y),de=G.x,Fe=G.y;break}case"C":{for(var Ae=J,be=j,ze=1;ze<N;ze++)r(J,j,Z,fe,_e,le,V,Y,ze/(N-1),G),k(Ae,be,G.x,G.y),Ae=G.x,be=G.y;break}}})}var a="precision highp float;attribute vec2 aUV;varying vec2 vUV;void main(){vUV=aUV;gl_Position=vec4(mix(vec2(-1.0),vec2(1.0),aUV),0.0,1.0);}",o="precision highp float;uniform sampler2D tex;varying vec2 vUV;void main(){gl_FragColor=texture2D(tex,vUV);}",l=new WeakMap,c={premultipliedAlpha:!1,preserveDrawingBuffer:!0,antialias:!1,depth:!1};function u(z,k){var N=z.getContext?z.getContext("webgl",c):z,G=l.get(N);if(!G){let fe=function(Ae){var be=J[Ae];if(!be&&(be=J[Ae]=N.getExtension(Ae),!be))throw new Error(Ae+" not supported");return be},_e=function(Ae,be){var ze=N.createShader(be);return N.shaderSource(ze,Ae),N.compileShader(ze),ze},le=function(Ae,be,ze,ge){if(!j[Ae]){var ke={},B={},ue=N.createProgram();N.attachShader(ue,_e(be,N.VERTEX_SHADER)),N.attachShader(ue,_e(ze,N.FRAGMENT_SHADER)),N.linkProgram(ue),j[Ae]={program:ue,transaction:function(ye){N.useProgram(ue),ye({setUniform:function(Te,D){for(var T=[],H=arguments.length-2;H-- >0;)T[H]=arguments[H+2];var Q=B[D]||(B[D]=N.getUniformLocation(ue,D));N["uniform"+Te].apply(N,[Q].concat(T))},setAttribute:function(Te,D,T,H,Q){var oe=ke[Te];oe||(oe=ke[Te]={buf:N.createBuffer(),loc:N.getAttribLocation(ue,Te),data:null}),N.bindBuffer(N.ARRAY_BUFFER,oe.buf),N.vertexAttribPointer(oe.loc,D,N.FLOAT,!1,0,0),N.enableVertexAttribArray(oe.loc),K?N.vertexAttribDivisor(oe.loc,H):fe("ANGLE_instanced_arrays").vertexAttribDivisorANGLE(oe.loc,H),Q!==oe.data&&(N.bufferData(N.ARRAY_BUFFER,Q,T),oe.data=Q)}})}}}j[Ae].transaction(ge)},de=function(Ae,be){Y++;try{N.activeTexture(N.TEXTURE0+Y);var ze=V[Ae];ze||(ze=V[Ae]=N.createTexture(),N.bindTexture(N.TEXTURE_2D,ze),N.texParameteri(N.TEXTURE_2D,N.TEXTURE_MIN_FILTER,N.NEAREST),N.texParameteri(N.TEXTURE_2D,N.TEXTURE_MAG_FILTER,N.NEAREST)),N.bindTexture(N.TEXTURE_2D,ze),be(ze,Y)}finally{Y--}},Fe=function(Ae,be,ze){var ge=N.createFramebuffer();Z.push(ge),N.bindFramebuffer(N.FRAMEBUFFER,ge),N.activeTexture(N.TEXTURE0+be),N.bindTexture(N.TEXTURE_2D,Ae),N.framebufferTexture2D(N.FRAMEBUFFER,N.COLOR_ATTACHMENT0,N.TEXTURE_2D,Ae,0);try{ze(ge)}finally{N.deleteFramebuffer(ge),N.bindFramebuffer(N.FRAMEBUFFER,Z[--Z.length-1]||null)}},Ne=function(){J={},j={},V={},Y=-1,Z.length=0};var K=typeof WebGL2RenderingContext<"u"&&N instanceof WebGL2RenderingContext,J={},j={},V={},Y=-1,Z=[];N.canvas.addEventListener("webglcontextlost",function(Ae){Ne(),Ae.preventDefault()},!1),l.set(N,G={gl:N,isWebGL2:K,getExtension:fe,withProgram:le,withTexture:de,withTextureFramebuffer:Fe,handleContextLoss:Ne})}k(G)}function f(z,k,N,G,K,J,j,V){j===void 0&&(j=15),V===void 0&&(V=null),u(z,function(Y){var Z=Y.gl,fe=Y.withProgram,_e=Y.withTexture;_e("copy",function(le,de){Z.texImage2D(Z.TEXTURE_2D,0,Z.RGBA,K,J,0,Z.RGBA,Z.UNSIGNED_BYTE,k),fe("copy",a,o,function(Fe){var Ne=Fe.setUniform,Ae=Fe.setAttribute;Ae("aUV",2,Z.STATIC_DRAW,0,new Float32Array([0,0,2,0,0,2])),Ne("1i","image",de),Z.bindFramebuffer(Z.FRAMEBUFFER,V||null),Z.disable(Z.BLEND),Z.colorMask(j&8,j&4,j&2,j&1),Z.viewport(N,G,K,J),Z.scissor(N,G,K,J),Z.drawArrays(Z.TRIANGLES,0,3)})})})}function h(z,k,N){var G=z.width,K=z.height;u(z,function(J){var j=J.gl,V=new Uint8Array(G*K*4);j.readPixels(0,0,G,K,j.RGBA,j.UNSIGNED_BYTE,V),z.width=k,z.height=N,f(j,V,0,0,G,K)})}var d=Object.freeze({__proto__:null,withWebGLContext:u,renderImageData:f,resizeWebGLCanvasWithoutClearing:h});function m(z,k,N,G,K,J){J===void 0&&(J=1);var j=new Uint8Array(z*k),V=G[2]-G[0],Y=G[3]-G[1],Z=[];s(N,function(Ae,be,ze,ge){Z.push({x1:Ae,y1:be,x2:ze,y2:ge,minX:Math.min(Ae,ze),minY:Math.min(be,ge),maxX:Math.max(Ae,ze),maxY:Math.max(be,ge)})}),Z.sort(function(Ae,be){return Ae.maxX-be.maxX});for(var fe=0;fe<z;fe++)for(var _e=0;_e<k;_e++){var le=Fe(G[0]+V*(fe+.5)/z,G[1]+Y*(_e+.5)/k),de=Math.pow(1-Math.abs(le)/K,J)/2;le<0&&(de=1-de),de=Math.max(0,Math.min(255,Math.round(de*255))),j[_e*z+fe]=de}return j;function Fe(Ae,be){for(var ze=1/0,ge=1/0,ke=Z.length;ke--;){var B=Z[ke];if(B.maxX+ge<=Ae)break;if(Ae+ge>B.minX&&be-ge<B.maxY&&be+ge>B.minY){var ue=_(Ae,be,B.x1,B.y1,B.x2,B.y2);ue<ze&&(ze=ue,ge=Math.sqrt(ze))}}return Ne(Ae,be)&&(ge=-ge),ge}function Ne(Ae,be){for(var ze=0,ge=Z.length;ge--;){var ke=Z[ge];if(ke.maxX<=Ae)break;var B=ke.y1>be!=ke.y2>be&&Ae<(ke.x2-ke.x1)*(be-ke.y1)/(ke.y2-ke.y1)+ke.x1;B&&(ze+=ke.y1<ke.y2?1:-1)}return ze!==0}}function g(z,k,N,G,K,J,j,V,Y,Z){J===void 0&&(J=1),V===void 0&&(V=0),Y===void 0&&(Y=0),Z===void 0&&(Z=0),p(z,k,N,G,K,J,j,null,V,Y,Z)}function p(z,k,N,G,K,J,j,V,Y,Z,fe){J===void 0&&(J=1),Y===void 0&&(Y=0),Z===void 0&&(Z=0),fe===void 0&&(fe=0);for(var _e=m(z,k,N,G,K,J),le=new Uint8Array(_e.length*4),de=0;de<_e.length;de++)le[de*4+fe]=_e[de];f(j,le,Y,Z,z,k,1<<3-fe,V)}function _(z,k,N,G,K,J){var j=K-N,V=J-G,Y=j*j+V*V,Z=Y?Math.max(0,Math.min(1,((z-N)*j+(k-G)*V)/Y)):0,fe=z-(N+Z*j),_e=k-(G+Z*V);return fe*fe+_e*_e}var M=Object.freeze({__proto__:null,generate:m,generateIntoCanvas:g,generateIntoFramebuffer:p}),y="precision highp float;uniform vec4 uGlyphBounds;attribute vec2 aUV;attribute vec4 aLineSegment;varying vec4 vLineSegment;varying vec2 vGlyphXY;void main(){vLineSegment=aLineSegment;vGlyphXY=mix(uGlyphBounds.xy,uGlyphBounds.zw,aUV);gl_Position=vec4(mix(vec2(-1.0),vec2(1.0),aUV),0.0,1.0);}",v="precision highp float;uniform vec4 uGlyphBounds;uniform float uMaxDistance;uniform float uExponent;varying vec4 vLineSegment;varying vec2 vGlyphXY;float absDistToSegment(vec2 point,vec2 lineA,vec2 lineB){vec2 lineDir=lineB-lineA;float lenSq=dot(lineDir,lineDir);float t=lenSq==0.0 ? 0.0 : clamp(dot(point-lineA,lineDir)/lenSq,0.0,1.0);vec2 linePt=lineA+t*lineDir;return distance(point,linePt);}void main(){vec4 seg=vLineSegment;vec2 p=vGlyphXY;float dist=absDistToSegment(p,seg.xy,seg.zw);float val=pow(1.0-clamp(dist/uMaxDistance,0.0,1.0),uExponent)*0.5;bool crossing=(seg.y>p.y!=seg.w>p.y)&&(p.x<(seg.z-seg.x)*(p.y-seg.y)/(seg.w-seg.y)+seg.x);bool crossingUp=crossing&&vLineSegment.y<vLineSegment.w;gl_FragColor=vec4(crossingUp ? 1.0/255.0 : 0.0,crossing&&!crossingUp ? 1.0/255.0 : 0.0,0.0,val);}",S="precision highp float;uniform sampler2D tex;varying vec2 vUV;void main(){vec4 color=texture2D(tex,vUV);bool inside=color.r!=color.g;float val=inside ? 1.0-color.a : color.a;gl_FragColor=vec4(val);}",b=new Float32Array([0,0,2,0,0,2]),E=null,x=!1,w={},R=new WeakMap;function L(z){if(!x&&!I(z))throw new Error("WebGL generation not supported")}function A(z,k,N,G,K,J,j){if(J===void 0&&(J=1),j===void 0&&(j=null),!j&&(j=E,!j)){var V=typeof OffscreenCanvas=="function"?new OffscreenCanvas(1,1):typeof document<"u"?document.createElement("canvas"):null;if(!V)throw new Error("OffscreenCanvas or DOM canvas not supported");j=E=V.getContext("webgl",{depth:!1})}L(j);var Y=new Uint8Array(z*k*4);u(j,function(le){var de=le.gl,Fe=le.withTexture,Ne=le.withTextureFramebuffer;Fe("readable",function(Ae,be){de.texImage2D(de.TEXTURE_2D,0,de.RGBA,z,k,0,de.RGBA,de.UNSIGNED_BYTE,null),Ne(Ae,be,function(ze){P(z,k,N,G,K,J,de,ze,0,0,0),de.readPixels(0,0,z,k,de.RGBA,de.UNSIGNED_BYTE,Y)})})});for(var Z=new Uint8Array(z*k),fe=0,_e=0;fe<Y.length;fe+=4)Z[_e++]=Y[fe];return Z}function U(z,k,N,G,K,J,j,V,Y,Z){J===void 0&&(J=1),V===void 0&&(V=0),Y===void 0&&(Y=0),Z===void 0&&(Z=0),P(z,k,N,G,K,J,j,null,V,Y,Z)}function P(z,k,N,G,K,J,j,V,Y,Z,fe){J===void 0&&(J=1),Y===void 0&&(Y=0),Z===void 0&&(Z=0),fe===void 0&&(fe=0),L(j);var _e=[];s(N,function(le,de,Fe,Ne){_e.push(le,de,Fe,Ne)}),_e=new Float32Array(_e),u(j,function(le){var de=le.gl,Fe=le.isWebGL2,Ne=le.getExtension,Ae=le.withProgram,be=le.withTexture,ze=le.withTextureFramebuffer,ge=le.handleContextLoss;if(be("rawDistances",function(ke,B){(z!==ke._lastWidth||k!==ke._lastHeight)&&de.texImage2D(de.TEXTURE_2D,0,de.RGBA,ke._lastWidth=z,ke._lastHeight=k,0,de.RGBA,de.UNSIGNED_BYTE,null),Ae("main",y,v,function(ue){var De=ue.setAttribute,ye=ue.setUniform,ce=!Fe&&Ne("ANGLE_instanced_arrays"),Te=!Fe&&Ne("EXT_blend_minmax");De("aUV",2,de.STATIC_DRAW,0,b),De("aLineSegment",4,de.DYNAMIC_DRAW,1,_e),ye.apply(void 0,["4f","uGlyphBounds"].concat(G)),ye("1f","uMaxDistance",K),ye("1f","uExponent",J),ze(ke,B,function(D){de.enable(de.BLEND),de.colorMask(!0,!0,!0,!0),de.viewport(0,0,z,k),de.scissor(0,0,z,k),de.blendFunc(de.ONE,de.ONE),de.blendEquationSeparate(de.FUNC_ADD,Fe?de.MAX:Te.MAX_EXT),de.clear(de.COLOR_BUFFER_BIT),Fe?de.drawArraysInstanced(de.TRIANGLES,0,3,_e.length/4):ce.drawArraysInstancedANGLE(de.TRIANGLES,0,3,_e.length/4)})}),Ae("post",a,S,function(ue){ue.setAttribute("aUV",2,de.STATIC_DRAW,0,b),ue.setUniform("1i","tex",B),de.bindFramebuffer(de.FRAMEBUFFER,V),de.disable(de.BLEND),de.colorMask(fe===0,fe===1,fe===2,fe===3),de.viewport(Y,Z,z,k),de.scissor(Y,Z,z,k),de.drawArrays(de.TRIANGLES,0,3)})}),de.isContextLost())throw ge(),new Error("webgl context lost")})}function I(z){var k=!z||z===E?w:z.canvas||z,N=R.get(k);if(N===void 0){x=!0;var G=null;try{var K=[97,106,97,61,99,137,118,80,80,118,137,99,61,97,106,97],J=A(4,4,"M8,8L16,8L24,24L16,24Z",[0,0,32,32],24,1,z);N=J&&K.length===J.length&&J.every(function(j,V){return j===K[V]}),N||(G="bad trial run results",console.info(K,J))}catch(j){N=!1,G=j.message}G&&console.warn("WebGL SDF generation not supported:",G),x=!1,R.set(k,N)}return N}var F=Object.freeze({__proto__:null,generate:A,generateIntoCanvas:U,generateIntoFramebuffer:P,isSupported:I});function O(z,k,N,G,K,J){K===void 0&&(K=Math.max(G[2]-G[0],G[3]-G[1])/2),J===void 0&&(J=1);try{return A.apply(F,arguments)}catch(j){return console.info("WebGL SDF generation failed, falling back to JS",j),m.apply(M,arguments)}}function q(z,k,N,G,K,J,j,V,Y,Z){K===void 0&&(K=Math.max(G[2]-G[0],G[3]-G[1])/2),J===void 0&&(J=1),V===void 0&&(V=0),Y===void 0&&(Y=0),Z===void 0&&(Z=0);try{return U.apply(F,arguments)}catch(fe){return console.info("WebGL SDF generation failed, falling back to JS",fe),g.apply(M,arguments)}}return e.forEachPathCommand=i,e.generate=O,e.generateIntoCanvas=q,e.javascript=M,e.pathToLineSegments=s,e.webgl=F,e.webglUtils=d,Object.defineProperty(e,"__esModule",{value:!0}),e})({});return n}function hb(){var n=(function(e){var t={R:"13k,1a,2,3,3,2+1j,ch+16,a+1,5+2,2+n,5,a,4,6+16,4+3,h+1b,4mo,179q,2+9,2+11,2i9+7y,2+68,4,3+4,5+13,4+3,2+4k,3+29,8+cf,1t+7z,w+17,3+3m,1t+3z,16o1+5r,8+30,8+mc,29+1r,29+4v,75+73",EN:"1c+9,3d+1,6,187+9,513,4+5,7+9,sf+j,175h+9,qw+q,161f+1d,4xt+a,25i+9",ES:"17,2,6dp+1,f+1,av,16vr,mx+1,4o,2",ET:"z+2,3h+3,b+1,ym,3e+1,2o,p4+1,8,6u,7c,g6,1wc,1n9+4,30+1b,2n,6d,qhx+1,h0m,a+1,49+2,63+1,4+1,6bb+3,12jj",AN:"16o+5,2j+9,2+1,35,ed,1ff2+9,87+u",CS:"18,2+1,b,2u,12k,55v,l,17v0,2,3,53,2+1,b",B:"a,3,f+2,2v,690",S:"9,2,k",WS:"c,k,4f4,1vk+a,u,1j,335",ON:"x+1,4+4,h+5,r+5,r+3,z,5+3,2+1,2+1,5,2+2,3+4,o,w,ci+1,8+d,3+d,6+8,2+g,39+1,9,6+1,2,33,b8,3+1,3c+1,7+1,5r,b,7h+3,sa+5,2,3i+6,jg+3,ur+9,2v,ij+1,9g+9,7+a,8m,4+1,49+x,14u,2+2,c+2,e+2,e+2,e+1,i+n,e+e,2+p,u+2,e+2,36+1,2+3,2+1,b,2+2,6+5,2,2,2,h+1,5+4,6+3,3+f,16+2,5+3l,3+81,1y+p,2+40,q+a,m+13,2r+ch,2+9e,75+hf,3+v,2+2w,6e+5,f+6,75+2a,1a+p,2+2g,d+5x,r+b,6+3,4+o,g,6+1,6+2,2k+1,4,2j,5h+z,1m+1,1e+f,t+2,1f+e,d+3,4o+3,2s+1,w,535+1r,h3l+1i,93+2,2s,b+1,3l+x,2v,4g+3,21+3,kz+1,g5v+1,5a,j+9,n+v,2,3,2+8,2+1,3+2,2,3,46+1,4+4,h+5,r+5,r+a,3h+2,4+6,b+4,78,1r+24,4+c,4,1hb,ey+6,103+j,16j+c,1ux+7,5+g,fsh,jdq+1t,4,57+2e,p1,1m,1m,1m,1m,4kt+1,7j+17,5+2r,d+e,3+e,2+e,2+10,m+4,w,1n+5,1q,4z+5,4b+rb,9+c,4+c,4+37,d+2g,8+b,l+b,5+1j,9+9,7+13,9+t,3+1,27+3c,2+29,2+3q,d+d,3+4,4+2,6+6,a+o,8+6,a+2,e+6,16+42,2+1i",BN:"0+8,6+d,2s+5,2+p,e,4m9,1kt+2,2b+5,5+5,17q9+v,7k,6p+8,6+1,119d+3,440+7,96s+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+1,1ekf+75,6p+2rz,1ben+1,1ekf+1,1ekf+1",NSM:"lc+33,7o+6,7c+18,2,2+1,2+1,2,21+a,1d+k,h,2u+6,3+5,3+1,2+3,10,v+q,2k+a,1n+8,a,p+3,2+8,2+2,2+4,18+2,3c+e,2+v,1k,2,5+7,5,4+6,b+1,u,1n,5+3,9,l+1,r,3+1,1m,5+1,5+1,3+2,4,v+1,4,c+1,1m,5+4,2+1,5,l+1,n+5,2,1n,3,2+3,9,8+1,c+1,v,1q,d,1f,4,1m+2,6+2,2+3,8+1,c+1,u,1n,g+1,l+1,t+1,1m+1,5+3,9,l+1,u,21,8+2,2,2j,3+6,d+7,2r,3+8,c+5,23+1,s,2,2,1k+d,2+4,2+1,6+a,2+z,a,2v+3,2+5,2+1,3+1,q+1,5+2,h+3,e,3+1,7,g,jk+2,qb+2,u+2,u+1,v+1,1t+1,2+6,9,3+a,a,1a+2,3c+1,z,3b+2,5+1,a,7+2,64+1,3,1n,2+6,2,2,3+7,7+9,3,1d+g,1s+3,1d,2+4,2,6,15+8,d+1,x+3,3+1,2+2,1l,2+1,4,2+2,1n+7,3+1,49+2,2+c,2+6,5,7,4+1,5j+1l,2+4,k1+w,2db+2,3y,2p+v,ff+3,30+1,n9x+3,2+9,x+1,29+1,7l,4,5,q+1,6,48+1,r+h,e,13+7,q+a,1b+2,1d,3+3,3+1,14,1w+5,3+1,3+1,d,9,1c,1g,2+2,3+1,6+1,2,17+1,9,6n,3,5,fn5,ki+f,h+f,r2,6b,46+4,1af+2,2+1,6+3,15+2,5,4m+1,fy+3,as+1,4a+a,4x,1j+e,1l+2,1e+3,3+1,1y+2,11+4,2+7,1r,d+1,1h+8,b+3,3,2o+2,3,2+1,7,4h,4+7,m+1,1m+1,4,12+6,4+4,5g+7,3+2,2,o,2d+5,2,5+1,2+1,6n+3,7+1,2+1,s+1,2e+7,3,2+1,2z,2,3+5,2,2u+2,3+3,2+4,78+8,2+1,75+1,2,5,41+3,3+1,5,x+5,3+1,15+5,3+3,9,a+5,3+2,1b+c,2+1,bb+6,2+5,2d+l,3+6,2+1,2+1,3f+5,4,2+1,2+6,2,21+1,4,2,9o+1,f0c+4,1o+6,t5,1s+3,2a,f5l+1,43t+2,i+7,3+6,v+3,45+2,1j0+1i,5+1d,9,f,n+4,2+e,11t+6,2+g,3+6,2+1,2+4,7a+6,c6+3,15t+6,32+6,gzhy+6n",AL:"16w,3,2,e+1b,z+2,2+2s,g+1,8+1,b+m,2+t,s+2i,c+e,4h+f,1d+1e,1bwe+dp,3+3z,x+c,2+1,35+3y,2rm+z,5+7,b+5,dt+l,c+u,17nl+27,1t+27,4x+6n,3+d",LRO:"6ct",RLO:"6cu",LRE:"6cq",RLE:"6cr",PDF:"6cs",LRI:"6ee",RLI:"6ef",FSI:"6eg",PDI:"6eh"},r={},i={};r.L=1,i[1]="L",Object.keys(t).forEach(function(ge,ke){r[ge]=1<<ke+1,i[r[ge]]=ge}),Object.freeze(r);var s=r.LRI|r.RLI|r.FSI,a=r.L|r.R|r.AL,o=r.B|r.S|r.WS|r.ON|r.FSI|r.LRI|r.RLI|r.PDI,l=r.BN|r.RLE|r.LRE|r.RLO|r.LRO|r.PDF,c=r.S|r.WS|r.B|s|r.PDI|l,u=null;function f(){if(!u){u=new Map;var ge=0;for(var ke in t)if(t.hasOwnProperty(ke))for(var B=t[ke],ue="",De=void 0,ye=!1,ce=0,Te=0;Te<=B.length+1;Te+=1){var D=B[Te];if(D!==","&&Te!==B.length)D==="+"?(ye=!0,ce=ge=ce+parseInt(ue,36),ue=""):ue+=D;else{ye?De=ge+parseInt(ue,36):(ce=ge=ce+parseInt(ue,36),De=ge),ye=!1,ue="",ce=De;for(var T=ge;T<De+1;T+=1)u.set(T,r[ke])}}}}function h(ge){return f(),u.get(ge.codePointAt(0))||r.L}function d(ge){return i[h(ge)]}var m={pairs:"14>1,1e>2,u>2,2wt>1,1>1,1ge>1,1wp>1,1j>1,f>1,hm>1,1>1,u>1,u6>1,1>1,+5,28>1,w>1,1>1,+3,b8>1,1>1,+3,1>3,-1>-1,3>1,1>1,+2,1s>1,1>1,x>1,th>1,1>1,+2,db>1,1>1,+3,3>1,1>1,+2,14qm>1,1>1,+1,4q>1,1e>2,u>2,2>1,+1",canonical:"6f1>-6dx,6dy>-6dx,6ec>-6ed,6ee>-6ed,6ww>2jj,-2ji>2jj,14r4>-1e7l,1e7m>-1e7l,1e7m>-1e5c,1e5d>-1e5b,1e5c>-14qx,14qy>-14qx,14vn>-1ecg,1ech>-1ecg,1edu>-1ecg,1eci>-1ecg,1eda>-1ecg,1eci>-1ecg,1eci>-168q,168r>-168q,168s>-14ye,14yf>-14ye"};function g(ge,ke){var B=36,ue=0,De=new Map,ye=ke&&new Map,ce;return ge.split(",").forEach(function Te(D){if(D.indexOf("+")!==-1)for(var T=+D;T--;)Te(ce);else{ce=D;var H=D.split(">"),Q=H[0],oe=H[1];Q=String.fromCodePoint(ue+=parseInt(Q,B)),oe=String.fromCodePoint(ue+=parseInt(oe,B)),De.set(Q,oe),ke&&ye.set(oe,Q)}}),{map:De,reverseMap:ye}}var p,_,M;function y(){if(!p){var ge=g(m.pairs,!0),ke=ge.map,B=ge.reverseMap;p=ke,_=B,M=g(m.canonical,!1).map}}function v(ge){return y(),p.get(ge)||null}function S(ge){return y(),_.get(ge)||null}function b(ge){return y(),M.get(ge)||null}var E=r.L,x=r.R,w=r.EN,R=r.ES,L=r.ET,A=r.AN,U=r.CS,P=r.B,I=r.S,F=r.ON,O=r.BN,q=r.NSM,z=r.AL,k=r.LRO,N=r.RLO,G=r.LRE,K=r.RLE,J=r.PDF,j=r.LRI,V=r.RLI,Y=r.FSI,Z=r.PDI;function fe(ge,ke){for(var B=125,ue=new Uint32Array(ge.length),De=0;De<ge.length;De++)ue[De]=h(ge[De]);var ye=new Map;function ce(bn,ri){var yn=ue[bn];ue[bn]=ri,ye.set(yn,ye.get(yn)-1),yn&o&&ye.set(o,ye.get(o)-1),ye.set(ri,(ye.get(ri)||0)+1),ri&o&&ye.set(o,(ye.get(o)||0)+1)}for(var Te=new Uint8Array(ge.length),D=new Map,T=[],H=null,Q=0;Q<ge.length;Q++)H||T.push(H={start:Q,end:ge.length-1,level:ke==="rtl"?1:ke==="ltr"?0:Yf(Q,!1)}),ue[Q]&P&&(H.end=Q,H=null);for(var oe=K|G|N|k|s|Z|J|P,me=function(bn){return bn+(bn&1?1:2)},Me=function(bn){return bn+(bn&1?2:1)},ee=0;ee<T.length;ee++){H=T[ee];var re=[{_level:H.level,_override:0,_isolate:0}],he=void 0,Re=0,ve=0,Se=0;ye.clear();for(var Ge=H.start;Ge<=H.end;Ge++){var Ce=ue[Ge];if(he=re[re.length-1],ye.set(Ce,(ye.get(Ce)||0)+1),Ce&o&&ye.set(o,(ye.get(o)||0)+1),Ce&oe)if(Ce&(K|G)){Te[Ge]=he._level;var Ye=(Ce===K?Me:me)(he._level);Ye<=B&&!Re&&!ve?re.push({_level:Ye,_override:0,_isolate:0}):Re||ve++}else if(Ce&(N|k)){Te[Ge]=he._level;var W=(Ce===N?Me:me)(he._level);W<=B&&!Re&&!ve?re.push({_level:W,_override:Ce&N?x:E,_isolate:0}):Re||ve++}else if(Ce&s){Ce&Y&&(Ce=Yf(Ge+1,!0)===1?V:j),Te[Ge]=he._level,he._override&&ce(Ge,he._override);var pe=(Ce===V?Me:me)(he._level);pe<=B&&Re===0&&ve===0?(Se++,re.push({_level:pe,_override:0,_isolate:1,_isolInitIndex:Ge})):Re++}else if(Ce&Z){if(Re>0)Re--;else if(Se>0){for(ve=0;!re[re.length-1]._isolate;)re.pop();var ie=re[re.length-1]._isolInitIndex;ie!=null&&(D.set(ie,Ge),D.set(Ge,ie)),re.pop(),Se--}he=re[re.length-1],Te[Ge]=he._level,he._override&&ce(Ge,he._override)}else Ce&J?(Re===0&&(ve>0?ve--:!he._isolate&&re.length>1&&(re.pop(),he=re[re.length-1])),Te[Ge]=he._level):Ce&P&&(Te[Ge]=H.level);else Te[Ge]=he._level,he._override&&Ce!==O&&ce(Ge,he._override)}for(var we=[],xe=null,ae=H.start;ae<=H.end;ae++){var Pe=ue[ae];if(!(Pe&l)){var Ke=Te[ae],st=Pe&s,Qe=Pe===Z;xe&&Ke===xe._level?(xe._end=ae,xe._endsWithIsolInit=st):we.push(xe={_start:ae,_end:ae,_level:Ke,_startsWithPDI:Qe,_endsWithIsolInit:st})}}for(var Ht=[],jt=0;jt<we.length;jt++){var Ln=we[jt];if(!Ln._startsWithPDI||Ln._startsWithPDI&&!D.has(Ln._start)){for(var di=[xe=Ln],pi=void 0;xe&&xe._endsWithIsolInit&&(pi=D.get(xe._end))!=null;)for(var qn=jt+1;qn<we.length;qn++)if(we[qn]._start===pi){di.push(xe=we[qn]);break}for(var Lt=[],ei=0;ei<di.length;ei++)for(var ea=di[ei],ts=ea._start;ts<=ea._end;ts++)Lt.push(ts);for(var ns=Te[Lt[0]],ta=H.level,Li=Lt[0]-1;Li>=0;Li--)if(!(ue[Li]&l)){ta=Te[Li];break}var is=Lt[Lt.length-1],eo=Te[is],to=H.level;if(!(ue[is]&s)){for(var rs=is+1;rs<=H.end;rs++)if(!(ue[rs]&l)){to=Te[rs];break}}Ht.push({_seqIndices:Lt,_sosType:Math.max(ta,ns)%2?x:E,_eosType:Math.max(to,eo)%2?x:E})}}for(var na=0;na<Ht.length;na++){var ia=Ht[na],Ze=ia._seqIndices,Er=ia._sosType,Yl=ia._eosType,C=Te[Ze[0]]&1?x:E;if(ye.get(q))for(var $=0;$<Ze.length;$++){var se=Ze[$];if(ue[se]&q){for(var te=Er,ne=$-1;ne>=0;ne--)if(!(ue[Ze[ne]]&l)){te=ue[Ze[ne]];break}ce(se,te&(s|Z)?F:te)}}if(ye.get(w))for(var Le=0;Le<Ze.length;Le++){var He=Ze[Le];if(ue[He]&w)for(var Ue=Le-1;Ue>=-1;Ue--){var Xe=Ue===-1?Er:ue[Ze[Ue]];if(Xe&a){Xe===z&&ce(He,A);break}}}if(ye.get(z))for(var qe=0;qe<Ze.length;qe++){var et=Ze[qe];ue[et]&z&&ce(et,x)}if(ye.get(R)||ye.get(U))for(var tt=1;tt<Ze.length-1;tt++){var je=Ze[tt];if(ue[je]&(R|U)){for(var ct=0,Rt=0,wt=tt-1;wt>=0&&(ct=ue[Ze[wt]],!!(ct&l));wt--);for(var mt=tt+1;mt<Ze.length&&(Rt=ue[Ze[mt]],!!(Rt&l));mt++);ct===Rt&&(ue[je]===R?ct===w:ct&(w|A))&&ce(je,ct)}}if(ye.get(w))for(var yt=0;yt<Ze.length;yt++){var Ve=Ze[yt];if(ue[Ve]&w){for(var tn=yt-1;tn>=0&&ue[Ze[tn]]&(L|l);tn--)ce(Ze[tn],w);for(yt++;yt<Ze.length&&ue[Ze[yt]]&(L|l|w);yt++)ue[Ze[yt]]!==w&&ce(Ze[yt],w)}}if(ye.get(L)||ye.get(R)||ye.get(U))for(var rt=0;rt<Ze.length;rt++){var _n=Ze[rt];if(ue[_n]&(L|R|U)){ce(_n,F);for(var vn=rt-1;vn>=0&&ue[Ze[vn]]&l;vn--)ce(Ze[vn],F);for(var In=rt+1;In<Ze.length&&ue[Ze[In]]&l;In++)ce(Ze[In],F)}}if(ye.get(w))for(var mi=0,_t=Er;mi<Ze.length;mi++){var Pt=Ze[mi],jn=ue[Pt];jn&w?_t===E&&ce(Pt,E):jn&a&&(_t=jn)}if(ye.get(o)){var dt=x|w|A,ti=dt|E,ni=[];{for(var Ii=[],ss=0;ss<Ze.length;ss++)if(ue[Ze[ss]]&o){var ra=ge[Ze[ss]],Of=void 0;if(v(ra)!==null)if(Ii.length<63)Ii.push({char:ra,seqIndex:ss});else break;else if((Of=S(ra))!==null)for(var sa=Ii.length-1;sa>=0;sa--){var ql=Ii[sa].char;if(ql===Of||ql===S(b(ra))||v(b(ql))===ra){ni.push([Ii[sa].seqIndex,ss]),Ii.length=sa;break}}}ni.sort(function(bn,ri){return bn[0]-ri[0]})}for(var jl=0;jl<ni.length;jl++){for(var Bf=ni[jl],no=Bf[0],Kl=Bf[1],kf=!1,ii=0,Zl=no+1;Zl<Kl;Zl++){var zf=Ze[Zl];if(ue[zf]&ti){kf=!0;var Gf=ue[zf]&dt?x:E;if(Gf===C){ii=Gf;break}}}if(kf&&!ii){ii=Er;for(var $l=no-1;$l>=0;$l--){var Hf=Ze[$l];if(ue[Hf]&ti){var Vf=ue[Hf]&dt?x:E;Vf!==C?ii=Vf:ii=C;break}}}if(ii){if(ue[Ze[no]]=ue[Ze[Kl]]=ii,ii!==C){for(var aa=no+1;aa<Ze.length;aa++)if(!(ue[Ze[aa]]&l)){h(ge[Ze[aa]])&q&&(ue[Ze[aa]]=ii);break}}if(ii!==C){for(var oa=Kl+1;oa<Ze.length;oa++)if(!(ue[Ze[oa]]&l)){h(ge[Ze[oa]])&q&&(ue[Ze[oa]]=ii);break}}}}for(var Qi=0;Qi<Ze.length;Qi++)if(ue[Ze[Qi]]&o){for(var Wf=Qi,Jl=Qi,Ql=Er,la=Qi-1;la>=0;la--)if(ue[Ze[la]]&l)Wf=la;else{Ql=ue[Ze[la]]&dt?x:E;break}for(var Xf=Yl,ca=Qi+1;ca<Ze.length;ca++)if(ue[Ze[ca]]&(o|l))Jl=ca;else{Xf=ue[Ze[ca]]&dt?x:E;break}for(var ec=Wf;ec<=Jl;ec++)ue[Ze[ec]]=Ql===Xf?Ql:C;Qi=Jl}}}for(var Fn=H.start;Fn<=H.end;Fn++){var Ng=Te[Fn],io=ue[Fn];if(Ng&1?io&(E|w|A)&&Te[Fn]++:io&x?Te[Fn]++:io&(A|w)&&(Te[Fn]+=2),io&l&&(Te[Fn]=Fn===0?H.level:Te[Fn-1]),Fn===H.end||h(ge[Fn])&(I|P))for(var ro=Fn;ro>=0&&h(ge[ro])&c;ro--)Te[ro]=H.level}}return{levels:Te,paragraphs:T};function Yf(bn,ri){for(var yn=bn;yn<ge.length;yn++){var er=ue[yn];if(er&(x|z))return 1;if(er&(P|E)||ri&&er===Z)return 0;if(er&s){var qf=Og(yn);yn=qf===-1?ge.length:qf}}return 0}function Og(bn){for(var ri=1,yn=bn+1;yn<ge.length;yn++){var er=ue[yn];if(er&P)break;if(er&Z){if(--ri===0)return yn}else er&s&&ri++}return-1}}var _e="14>1,j>2,t>2,u>2,1a>g,2v3>1,1>1,1ge>1,1wd>1,b>1,1j>1,f>1,ai>3,-2>3,+1,8>1k0,-1jq>1y7,-1y6>1hf,-1he>1h6,-1h5>1ha,-1h8>1qi,-1pu>1,6>3u,-3s>7,6>1,1>1,f>1,1>1,+2,3>1,1>1,+13,4>1,1>1,6>1eo,-1ee>1,3>1mg,-1me>1mk,-1mj>1mi,-1mg>1mi,-1md>1,1>1,+2,1>10k,-103>1,1>1,4>1,5>1,1>1,+10,3>1,1>8,-7>8,+1,-6>7,+1,a>1,1>1,u>1,u6>1,1>1,+5,26>1,1>1,2>1,2>2,8>1,7>1,4>1,1>1,+5,b8>1,1>1,+3,1>3,-2>1,2>1,1>1,+2,c>1,3>1,1>1,+2,h>1,3>1,a>1,1>1,2>1,3>1,1>1,d>1,f>1,3>1,1a>1,1>1,6>1,7>1,13>1,k>1,1>1,+19,4>1,1>1,+2,2>1,1>1,+18,m>1,a>1,1>1,lk>1,1>1,4>1,2>1,f>1,3>1,1>1,+3,db>1,1>1,+3,3>1,1>1,+2,14qm>1,1>1,+1,6>1,4j>1,j>2,t>2,u>2,2>1,+1",le;function de(){if(!le){var ge=g(_e,!0),ke=ge.map,B=ge.reverseMap;B.forEach(function(ue,De){ke.set(De,ue)}),le=ke}}function Fe(ge){return de(),le.get(ge)||null}function Ne(ge,ke,B,ue){var De=ge.length;B=Math.max(0,B==null?0:+B),ue=Math.min(De-1,ue==null?De-1:+ue);for(var ye=new Map,ce=B;ce<=ue;ce++)if(ke[ce]&1){var Te=Fe(ge[ce]);Te!==null&&ye.set(ce,Te)}return ye}function Ae(ge,ke,B,ue){var De=ge.length;B=Math.max(0,B==null?0:+B),ue=Math.min(De-1,ue==null?De-1:+ue);var ye=[];return ke.paragraphs.forEach(function(ce){var Te=Math.max(B,ce.start),D=Math.min(ue,ce.end);if(Te<D){for(var T=ke.levels.slice(Te,D+1),H=D;H>=Te&&h(ge[H])&c;H--)T[H]=ce.level;for(var Q=ce.level,oe=1/0,me=0;me<T.length;me++){var Me=T[me];Me>Q&&(Q=Me),Me<oe&&(oe=Me|1)}for(var ee=Q;ee>=oe;ee--)for(var re=0;re<T.length;re++)if(T[re]>=ee){for(var he=re;re+1<T.length&&T[re+1]>=ee;)re++;re>he&&ye.push([he+Te,re+Te])}}}),ye}function be(ge,ke,B,ue){var De=ze(ge,ke,B,ue),ye=[].concat(ge);return De.forEach(function(ce,Te){ye[Te]=(ke.levels[ce]&1?Fe(ge[ce]):null)||ge[ce]}),ye.join("")}function ze(ge,ke,B,ue){for(var De=Ae(ge,ke,B,ue),ye=[],ce=0;ce<ge.length;ce++)ye[ce]=ce;return De.forEach(function(Te){for(var D=Te[0],T=Te[1],H=ye.slice(D,T+1),Q=H.length;Q--;)ye[T-Q]=H[Q]}),ye}return e.closingToOpeningBracket=S,e.getBidiCharType=h,e.getBidiCharTypeName=d,e.getCanonicalBracket=b,e.getEmbeddingLevels=fe,e.getMirroredCharacter=Fe,e.getMirroredCharactersMap=Ne,e.getReorderSegments=Ae,e.getReorderedIndices=ze,e.getReorderedString=be,e.openingToClosingBracket=v,Object.defineProperty(e,"__esModule",{value:!0}),e})({});return n}const $m=/\bvoid\s+main\s*\(\s*\)\s*{/g;function gh(n){const e=/^[ \t]*#include +<([\w\d./]+)>/gm;function t(r,i){let s=it[i];return s?gh(s):r}return n.replace(e,t)}const ln=[];for(let n=0;n<256;n++)ln[n]=(n<16?"0":"")+n.toString(16);function fb(){const n=Math.random()*4294967295|0,e=Math.random()*4294967295|0,t=Math.random()*4294967295|0,r=Math.random()*4294967295|0;return(ln[n&255]+ln[n>>8&255]+ln[n>>16&255]+ln[n>>24&255]+"-"+ln[e&255]+ln[e>>8&255]+"-"+ln[e>>16&15|64]+ln[e>>24&255]+"-"+ln[t&63|128]+ln[t>>8&255]+"-"+ln[t>>16&255]+ln[t>>24&255]+ln[r&255]+ln[r>>8&255]+ln[r>>16&255]+ln[r>>24&255]).toUpperCase()}const Dr=Object.assign||function(){let n=arguments[0];for(let e=1,t=arguments.length;e<t;e++){let r=arguments[e];if(r)for(let i in r)Object.prototype.hasOwnProperty.call(r,i)&&(n[i]=r[i])}return n},db=Date.now(),ep=new WeakMap,tp=new Map;let pb=1e10;function _h(n,e){const t=vb(e);let r=ep.get(n);if(r||ep.set(n,r=Object.create(null)),r[t])return new r[t];const i=`_onBeforeCompile${t}`,s=function(c,u){n.onBeforeCompile.call(this,c,u);const f=this.customProgramCacheKey()+"|"+c.vertexShader+"|"+c.fragmentShader;let h=tp[f];if(!h){const d=mb(this,c,e,t);h=tp[f]=d}c.vertexShader=h.vertexShader,c.fragmentShader=h.fragmentShader,Dr(c.uniforms,this.uniforms),e.timeUniform&&(c.uniforms[e.timeUniform]={get value(){return Date.now()-db}}),this[i]&&this[i](c)},a=function(){return o(e.chained?n:n.clone())},o=function(c){const u=Object.create(c,l);return Object.defineProperty(u,"baseMaterial",{value:n}),Object.defineProperty(u,"id",{value:pb++}),u.uuid=fb(),u.uniforms=Dr({},c.uniforms,e.uniforms),u.defines=Dr({},c.defines,e.defines),u.defines[`TROIKA_DERIVED_MATERIAL_${t}`]="",u.extensions=Dr({},c.extensions,e.extensions),u._listeners=void 0,u},l={constructor:{value:a},isDerivedMaterial:{value:!0},type:{get:()=>n.type,set:c=>{n.type=c}},isDerivedFrom:{writable:!0,configurable:!0,value:function(c){const u=this.baseMaterial;return c===u||u.isDerivedMaterial&&u.isDerivedFrom(c)||!1}},customProgramCacheKey:{writable:!0,configurable:!0,value:function(){return n.customProgramCacheKey()+"|"+t}},onBeforeCompile:{get(){return s},set(c){this[i]=c}},copy:{writable:!0,configurable:!0,value:function(c){return n.copy.call(this,c),!n.isShaderMaterial&&!n.isDerivedMaterial&&(Dr(this.extensions,c.extensions),Dr(this.defines,c.defines),Dr(this.uniforms,Om.clone(c.uniforms))),this}},clone:{writable:!0,configurable:!0,value:function(){const c=new n.constructor;return o(c).copy(this)}},getDepthMaterial:{writable:!0,configurable:!0,value:function(){let c=this._depthMaterial;return c||(c=this._depthMaterial=_h(n.isDerivedMaterial?n.getDepthMaterial():new Bm({depthPacking:f_}),e),c.defines.IS_DEPTH_MATERIAL="",c.uniforms=this.uniforms),c}},getDistanceMaterial:{writable:!0,configurable:!0,value:function(){let c=this._distanceMaterial;return c||(c=this._distanceMaterial=_h(n.isDerivedMaterial?n.getDistanceMaterial():new km,e),c.defines.IS_DISTANCE_MATERIAL="",c.uniforms=this.uniforms),c}},dispose:{writable:!0,configurable:!0,value(){const{_depthMaterial:c,_distanceMaterial:u}=this;c&&c.dispose(),u&&u.dispose(),n.dispose.call(this)}}};return r[t]=a,new a}function mb(n,{vertexShader:e,fragmentShader:t},r,i){let{vertexDefs:s,vertexMainIntro:a,vertexMainOutro:o,vertexTransform:l,fragmentDefs:c,fragmentMainIntro:u,fragmentMainOutro:f,fragmentColorTransform:h,customRewriter:d,timeUniform:m}=r;if(s=s||"",a=a||"",o=o||"",c=c||"",u=u||"",f=f||"",(l||d)&&(e=gh(e)),(h||d)&&(t=t.replace(/^[ \t]*#include <((?:tonemapping|encodings|colorspace|fog|premultiplied_alpha|dithering)_fragment)>/gm,`
//!BEGIN_POST_CHUNK $1
$&
//!END_POST_CHUNK
`),t=gh(t)),d){let g=d({vertexShader:e,fragmentShader:t});e=g.vertexShader,t=g.fragmentShader}if(h){let g=[];t=t.replace(/^\/\/!BEGIN_POST_CHUNK[^]+?^\/\/!END_POST_CHUNK/gm,p=>(g.push(p),"")),f=`${h}
${g.join(`
`)}
${f}`}if(m){const g=`
uniform float ${m};
`;s=g+s,c=g+c}return l&&(e=`vec3 troika_position_${i};
vec3 troika_normal_${i};
vec2 troika_uv_${i};
${e}
`,s=`${s}
void troikaVertexTransform${i}() {
  vec3 position = troika_position_${i};
  vec3 normal = troika_normal_${i};
  vec2 uv = troika_uv_${i};
  ${l}
  troika_position_${i} = position;
  troika_normal_${i} = normal;
  troika_uv_${i} = uv;
}
`,a=`
troika_position_${i} = vec3(position);
troika_normal_${i} = vec3(normal);
troika_uv_${i} = vec2(uv);
troikaVertexTransform${i}();
${a}
`,e=e.replace(/\b(position|normal|uv)\b/g,(g,p,_,M)=>/\battribute\s+vec[23]\s+$/.test(M.substr(0,_))?p:`troika_${p}_${i}`),n.map&&n.map.channel>0||(e=e.replace(/\bMAP_UV\b/g,`troika_uv_${i}`))),e=np(e,i,s,a,o),t=np(t,i,c,u,f),{vertexShader:e,fragmentShader:t}}function np(n,e,t,r,i){return(r||i||t)&&(n=n.replace($m,`
${t}
void troikaOrigMain${e}() {`),n+=`
void main() {
  ${r}
  troikaOrigMain${e}();
  ${i}
}`),n}function gb(n,e){return n==="uniforms"?void 0:typeof e=="function"?e.toString():e}let _b=0;const ip=new Map;function vb(n){const e=JSON.stringify(n,gb);let t=ip.get(e);return t==null&&ip.set(e,t=++_b),t}/*!
Custom build of Typr.ts (https://github.com/fredli74/Typr.ts) for use in Troika text rendering.
Original MIT license applies: https://github.com/fredli74/Typr.ts/blob/master/LICENSE
*/function xb(){return typeof window>"u"&&(self.window=self),(function(n){var e={parse:function(i){var s=e._bin,a=new Uint8Array(i);if(s.readASCII(a,0,4)=="ttcf"){var o=4;s.readUshort(a,o),o+=2,s.readUshort(a,o),o+=2;var l=s.readUint(a,o);o+=4;for(var c=[],u=0;u<l;u++){var f=s.readUint(a,o);o+=4,c.push(e._readFont(a,f))}return c}return[e._readFont(a,0)]},_readFont:function(i,s){var a=e._bin,o=s;a.readFixed(i,s),s+=4;var l=a.readUshort(i,s);s+=2,a.readUshort(i,s),s+=2,a.readUshort(i,s),s+=2,a.readUshort(i,s),s+=2;for(var c=["cmap","head","hhea","maxp","hmtx","name","OS/2","post","loca","glyf","kern","CFF ","GDEF","GPOS","GSUB","SVG "],u={_data:i,_offset:o},f={},h=0;h<l;h++){var d=a.readASCII(i,s,4);s+=4,a.readUint(i,s),s+=4;var m=a.readUint(i,s);s+=4;var g=a.readUint(i,s);s+=4,f[d]={offset:m,length:g}}for(h=0;h<c.length;h++){var p=c[h];f[p]&&(u[p.trim()]=e[p.trim()].parse(i,f[p].offset,f[p].length,u))}return u},_tabOffset:function(i,s,a){for(var o=e._bin,l=o.readUshort(i,a+4),c=a+12,u=0;u<l;u++){var f=o.readASCII(i,c,4);c+=4,o.readUint(i,c),c+=4;var h=o.readUint(i,c);if(c+=4,o.readUint(i,c),c+=4,f==s)return h}return 0}};e._bin={readFixed:function(i,s){return(i[s]<<8|i[s+1])+(i[s+2]<<8|i[s+3])/65540},readF2dot14:function(i,s){return e._bin.readShort(i,s)/16384},readInt:function(i,s){return e._bin._view(i).getInt32(s)},readInt8:function(i,s){return e._bin._view(i).getInt8(s)},readShort:function(i,s){return e._bin._view(i).getInt16(s)},readUshort:function(i,s){return e._bin._view(i).getUint16(s)},readUshorts:function(i,s,a){for(var o=[],l=0;l<a;l++)o.push(e._bin.readUshort(i,s+2*l));return o},readUint:function(i,s){return e._bin._view(i).getUint32(s)},readUint64:function(i,s){return 4294967296*e._bin.readUint(i,s)+e._bin.readUint(i,s+4)},readASCII:function(i,s,a){for(var o="",l=0;l<a;l++)o+=String.fromCharCode(i[s+l]);return o},readUnicode:function(i,s,a){for(var o="",l=0;l<a;l++){var c=i[s++]<<8|i[s++];o+=String.fromCharCode(c)}return o},_tdec:typeof window<"u"&&window.TextDecoder?new window.TextDecoder:null,readUTF8:function(i,s,a){var o=e._bin._tdec;return o&&s==0&&a==i.length?o.decode(i):e._bin.readASCII(i,s,a)},readBytes:function(i,s,a){for(var o=[],l=0;l<a;l++)o.push(i[s+l]);return o},readASCIIArray:function(i,s,a){for(var o=[],l=0;l<a;l++)o.push(String.fromCharCode(i[s+l]));return o},_view:function(i){return i._dataView||(i._dataView=i.buffer?new DataView(i.buffer,i.byteOffset,i.byteLength):new DataView(new Uint8Array(i).buffer))}},e._lctf={},e._lctf.parse=function(i,s,a,o,l){var c=e._bin,u={},f=s;c.readFixed(i,s),s+=4;var h=c.readUshort(i,s);s+=2;var d=c.readUshort(i,s);s+=2;var m=c.readUshort(i,s);return s+=2,u.scriptList=e._lctf.readScriptList(i,f+h),u.featureList=e._lctf.readFeatureList(i,f+d),u.lookupList=e._lctf.readLookupList(i,f+m,l),u},e._lctf.readLookupList=function(i,s,a){var o=e._bin,l=s,c=[],u=o.readUshort(i,s);s+=2;for(var f=0;f<u;f++){var h=o.readUshort(i,s);s+=2;var d=e._lctf.readLookupTable(i,l+h,a);c.push(d)}return c},e._lctf.readLookupTable=function(i,s,a){var o=e._bin,l=s,c={tabs:[]};c.ltype=o.readUshort(i,s),s+=2,c.flag=o.readUshort(i,s),s+=2;var u=o.readUshort(i,s);s+=2;for(var f=c.ltype,h=0;h<u;h++){var d=o.readUshort(i,s);s+=2;var m=a(i,f,l+d,c);c.tabs.push(m)}return c},e._lctf.numOfOnes=function(i){for(var s=0,a=0;a<32;a++)(i>>>a&1)!=0&&s++;return s},e._lctf.readClassDef=function(i,s){var a=e._bin,o=[],l=a.readUshort(i,s);if(s+=2,l==1){var c=a.readUshort(i,s);s+=2;var u=a.readUshort(i,s);s+=2;for(var f=0;f<u;f++)o.push(c+f),o.push(c+f),o.push(a.readUshort(i,s)),s+=2}if(l==2){var h=a.readUshort(i,s);for(s+=2,f=0;f<h;f++)o.push(a.readUshort(i,s)),s+=2,o.push(a.readUshort(i,s)),s+=2,o.push(a.readUshort(i,s)),s+=2}return o},e._lctf.getInterval=function(i,s){for(var a=0;a<i.length;a+=3){var o=i[a],l=i[a+1];if(i[a+2],o<=s&&s<=l)return a}return-1},e._lctf.readCoverage=function(i,s){var a=e._bin,o={};o.fmt=a.readUshort(i,s),s+=2;var l=a.readUshort(i,s);return s+=2,o.fmt==1&&(o.tab=a.readUshorts(i,s,l)),o.fmt==2&&(o.tab=a.readUshorts(i,s,3*l)),o},e._lctf.coverageIndex=function(i,s){var a=i.tab;if(i.fmt==1)return a.indexOf(s);if(i.fmt==2){var o=e._lctf.getInterval(a,s);if(o!=-1)return a[o+2]+(s-a[o])}return-1},e._lctf.readFeatureList=function(i,s){var a=e._bin,o=s,l=[],c=a.readUshort(i,s);s+=2;for(var u=0;u<c;u++){var f=a.readASCII(i,s,4);s+=4;var h=a.readUshort(i,s);s+=2;var d=e._lctf.readFeatureTable(i,o+h);d.tag=f.trim(),l.push(d)}return l},e._lctf.readFeatureTable=function(i,s){var a=e._bin,o=s,l={},c=a.readUshort(i,s);s+=2,c>0&&(l.featureParams=o+c);var u=a.readUshort(i,s);s+=2,l.tab=[];for(var f=0;f<u;f++)l.tab.push(a.readUshort(i,s+2*f));return l},e._lctf.readScriptList=function(i,s){var a=e._bin,o=s,l={},c=a.readUshort(i,s);s+=2;for(var u=0;u<c;u++){var f=a.readASCII(i,s,4);s+=4;var h=a.readUshort(i,s);s+=2,l[f.trim()]=e._lctf.readScriptTable(i,o+h)}return l},e._lctf.readScriptTable=function(i,s){var a=e._bin,o=s,l={},c=a.readUshort(i,s);s+=2,c>0&&(l.default=e._lctf.readLangSysTable(i,o+c));var u=a.readUshort(i,s);s+=2;for(var f=0;f<u;f++){var h=a.readASCII(i,s,4);s+=4;var d=a.readUshort(i,s);s+=2,l[h.trim()]=e._lctf.readLangSysTable(i,o+d)}return l},e._lctf.readLangSysTable=function(i,s){var a=e._bin,o={};a.readUshort(i,s),s+=2,o.reqFeature=a.readUshort(i,s),s+=2;var l=a.readUshort(i,s);return s+=2,o.features=a.readUshorts(i,s,l),o},e.CFF={},e.CFF.parse=function(i,s,a){var o=e._bin;(i=new Uint8Array(i.buffer,s,a))[s=0],i[++s],i[++s],i[++s],s++;var l=[];s=e.CFF.readIndex(i,s,l);for(var c=[],u=0;u<l.length-1;u++)c.push(o.readASCII(i,s+l[u],l[u+1]-l[u]));s+=l[l.length-1];var f=[];s=e.CFF.readIndex(i,s,f);var h=[];for(u=0;u<f.length-1;u++)h.push(e.CFF.readDict(i,s+f[u],s+f[u+1]));s+=f[f.length-1];var d=h[0],m=[];s=e.CFF.readIndex(i,s,m);var g=[];for(u=0;u<m.length-1;u++)g.push(o.readASCII(i,s+m[u],m[u+1]-m[u]));if(s+=m[m.length-1],e.CFF.readSubrs(i,s,d),d.CharStrings){s=d.CharStrings,m=[],s=e.CFF.readIndex(i,s,m);var p=[];for(u=0;u<m.length-1;u++)p.push(o.readBytes(i,s+m[u],m[u+1]-m[u]));d.CharStrings=p}if(d.ROS){s=d.FDArray;var _=[];for(s=e.CFF.readIndex(i,s,_),d.FDArray=[],u=0;u<_.length-1;u++){var M=e.CFF.readDict(i,s+_[u],s+_[u+1]);e.CFF._readFDict(i,M,g),d.FDArray.push(M)}s+=_[_.length-1],s=d.FDSelect,d.FDSelect=[];var y=i[s];if(s++,y!=3)throw y;var v=o.readUshort(i,s);for(s+=2,u=0;u<v+1;u++)d.FDSelect.push(o.readUshort(i,s),i[s+2]),s+=3}return d.Encoding&&(d.Encoding=e.CFF.readEncoding(i,d.Encoding,d.CharStrings.length)),d.charset&&(d.charset=e.CFF.readCharset(i,d.charset,d.CharStrings.length)),e.CFF._readFDict(i,d,g),d},e.CFF._readFDict=function(i,s,a){var o;for(var l in s.Private&&(o=s.Private[1],s.Private=e.CFF.readDict(i,o,o+s.Private[0]),s.Private.Subrs&&e.CFF.readSubrs(i,o+s.Private.Subrs,s.Private)),s)["FamilyName","FontName","FullName","Notice","version","Copyright"].indexOf(l)!=-1&&(s[l]=a[s[l]-426+35])},e.CFF.readSubrs=function(i,s,a){var o=e._bin,l=[];s=e.CFF.readIndex(i,s,l);var c,u=l.length;c=u<1240?107:u<33900?1131:32768,a.Bias=c,a.Subrs=[];for(var f=0;f<l.length-1;f++)a.Subrs.push(o.readBytes(i,s+l[f],l[f+1]-l[f]))},e.CFF.tableSE=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,0,111,112,113,114,0,115,116,117,118,119,120,121,122,0,123,0,124,125,126,127,128,129,130,131,0,132,133,0,134,135,136,137,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,138,0,139,0,0,0,0,140,141,142,143,0,0,0,0,0,144,0,0,0,145,0,0,146,147,148,149,0,0,0,0],e.CFF.glyphByUnicode=function(i,s){for(var a=0;a<i.charset.length;a++)if(i.charset[a]==s)return a;return-1},e.CFF.glyphBySE=function(i,s){return s<0||s>255?-1:e.CFF.glyphByUnicode(i,e.CFF.tableSE[s])},e.CFF.readEncoding=function(i,s,a){e._bin;var o=[".notdef"],l=i[s];if(s++,l!=0)throw"error: unknown encoding format: "+l;var c=i[s];s++;for(var u=0;u<c;u++)o.push(i[s+u]);return o},e.CFF.readCharset=function(i,s,a){var o=e._bin,l=[".notdef"],c=i[s];if(s++,c==0)for(var u=0;u<a;u++){var f=o.readUshort(i,s);s+=2,l.push(f)}else{if(c!=1&&c!=2)throw"error: format: "+c;for(;l.length<a;){f=o.readUshort(i,s),s+=2;var h=0;for(c==1?(h=i[s],s++):(h=o.readUshort(i,s),s+=2),u=0;u<=h;u++)l.push(f),f++}}return l},e.CFF.readIndex=function(i,s,a){var o=e._bin,l=o.readUshort(i,s)+1,c=i[s+=2];if(s++,c==1)for(var u=0;u<l;u++)a.push(i[s+u]);else if(c==2)for(u=0;u<l;u++)a.push(o.readUshort(i,s+2*u));else if(c==3)for(u=0;u<l;u++)a.push(16777215&o.readUint(i,s+3*u-1));else if(l!=1)throw"unsupported offset size: "+c+", count: "+l;return(s+=l*c)-1},e.CFF.getCharString=function(i,s,a){var o=e._bin,l=i[s],c=i[s+1];i[s+2],i[s+3],i[s+4];var u=1,f=null,h=null;l<=20&&(f=l,u=1),l==12&&(f=100*l+c,u=2),21<=l&&l<=27&&(f=l,u=1),l==28&&(h=o.readShort(i,s+1),u=3),29<=l&&l<=31&&(f=l,u=1),32<=l&&l<=246&&(h=l-139,u=1),247<=l&&l<=250&&(h=256*(l-247)+c+108,u=2),251<=l&&l<=254&&(h=256*-(l-251)-c-108,u=2),l==255&&(h=o.readInt(i,s+1)/65535,u=5),a.val=h??"o"+f,a.size=u},e.CFF.readCharString=function(i,s,a){for(var o=s+a,l=e._bin,c=[];s<o;){var u=i[s],f=i[s+1];i[s+2],i[s+3],i[s+4];var h=1,d=null,m=null;u<=20&&(d=u,h=1),u==12&&(d=100*u+f,h=2),u!=19&&u!=20||(d=u,h=2),21<=u&&u<=27&&(d=u,h=1),u==28&&(m=l.readShort(i,s+1),h=3),29<=u&&u<=31&&(d=u,h=1),32<=u&&u<=246&&(m=u-139,h=1),247<=u&&u<=250&&(m=256*(u-247)+f+108,h=2),251<=u&&u<=254&&(m=256*-(u-251)-f-108,h=2),u==255&&(m=l.readInt(i,s+1)/65535,h=5),c.push(m??"o"+d),s+=h}return c},e.CFF.readDict=function(i,s,a){for(var o=e._bin,l={},c=[];s<a;){var u=i[s],f=i[s+1];i[s+2],i[s+3],i[s+4];var h=1,d=null,m=null;if(u==28&&(m=o.readShort(i,s+1),h=3),u==29&&(m=o.readInt(i,s+1),h=5),32<=u&&u<=246&&(m=u-139,h=1),247<=u&&u<=250&&(m=256*(u-247)+f+108,h=2),251<=u&&u<=254&&(m=256*-(u-251)-f-108,h=2),u==255)throw m=o.readInt(i,s+1)/65535,h=5,"unknown number";if(u==30){var g=[];for(h=1;;){var p=i[s+h];h++;var _=p>>4,M=15&p;if(_!=15&&g.push(_),M!=15&&g.push(M),M==15)break}for(var y="",v=[0,1,2,3,4,5,6,7,8,9,".","e","e-","reserved","-","endOfNumber"],S=0;S<g.length;S++)y+=v[g[S]];m=parseFloat(y)}u<=21&&(d=["version","Notice","FullName","FamilyName","Weight","FontBBox","BlueValues","OtherBlues","FamilyBlues","FamilyOtherBlues","StdHW","StdVW","escape","UniqueID","XUID","charset","Encoding","CharStrings","Private","Subrs","defaultWidthX","nominalWidthX"][u],h=1,u==12&&(d=["Copyright","isFixedPitch","ItalicAngle","UnderlinePosition","UnderlineThickness","PaintType","CharstringType","FontMatrix","StrokeWidth","BlueScale","BlueShift","BlueFuzz","StemSnapH","StemSnapV","ForceBold",0,0,"LanguageGroup","ExpansionFactor","initialRandomSeed","SyntheticBase","PostScript","BaseFontName","BaseFontBlend",0,0,0,0,0,0,"ROS","CIDFontVersion","CIDFontRevision","CIDFontType","CIDCount","UIDBase","FDArray","FDSelect","FontName"][f],h=2)),d!=null?(l[d]=c.length==1?c[0]:c,c=[]):c.push(m),s+=h}return l},e.cmap={},e.cmap.parse=function(i,s,a){i=new Uint8Array(i.buffer,s,a),s=0;var o=e._bin,l={};o.readUshort(i,s),s+=2;var c=o.readUshort(i,s);s+=2;var u=[];l.tables=[];for(var f=0;f<c;f++){var h=o.readUshort(i,s);s+=2;var d=o.readUshort(i,s);s+=2;var m=o.readUint(i,s);s+=4;var g="p"+h+"e"+d,p=u.indexOf(m);if(p==-1){var _;p=l.tables.length,u.push(m);var M=o.readUshort(i,m);M==0?_=e.cmap.parse0(i,m):M==4?_=e.cmap.parse4(i,m):M==6?_=e.cmap.parse6(i,m):M==12?_=e.cmap.parse12(i,m):console.debug("unknown format: "+M,h,d,m),l.tables.push(_)}if(l[g]!=null)throw"multiple tables for one platform+encoding";l[g]=p}return l},e.cmap.parse0=function(i,s){var a=e._bin,o={};o.format=a.readUshort(i,s),s+=2;var l=a.readUshort(i,s);s+=2,a.readUshort(i,s),s+=2,o.map=[];for(var c=0;c<l-6;c++)o.map.push(i[s+c]);return o},e.cmap.parse4=function(i,s){var a=e._bin,o=s,l={};l.format=a.readUshort(i,s),s+=2;var c=a.readUshort(i,s);s+=2,a.readUshort(i,s),s+=2;var u=a.readUshort(i,s);s+=2;var f=u/2;l.searchRange=a.readUshort(i,s),s+=2,l.entrySelector=a.readUshort(i,s),s+=2,l.rangeShift=a.readUshort(i,s),s+=2,l.endCount=a.readUshorts(i,s,f),s+=2*f,s+=2,l.startCount=a.readUshorts(i,s,f),s+=2*f,l.idDelta=[];for(var h=0;h<f;h++)l.idDelta.push(a.readShort(i,s)),s+=2;for(l.idRangeOffset=a.readUshorts(i,s,f),s+=2*f,l.glyphIdArray=[];s<o+c;)l.glyphIdArray.push(a.readUshort(i,s)),s+=2;return l},e.cmap.parse6=function(i,s){var a=e._bin,o={};o.format=a.readUshort(i,s),s+=2,a.readUshort(i,s),s+=2,a.readUshort(i,s),s+=2,o.firstCode=a.readUshort(i,s),s+=2;var l=a.readUshort(i,s);s+=2,o.glyphIdArray=[];for(var c=0;c<l;c++)o.glyphIdArray.push(a.readUshort(i,s)),s+=2;return o},e.cmap.parse12=function(i,s){var a=e._bin,o={};o.format=a.readUshort(i,s),s+=2,s+=2,a.readUint(i,s),s+=4,a.readUint(i,s),s+=4;var l=a.readUint(i,s);s+=4,o.groups=[];for(var c=0;c<l;c++){var u=s+12*c,f=a.readUint(i,u+0),h=a.readUint(i,u+4),d=a.readUint(i,u+8);o.groups.push([f,h,d])}return o},e.glyf={},e.glyf.parse=function(i,s,a,o){for(var l=[],c=0;c<o.maxp.numGlyphs;c++)l.push(null);return l},e.glyf._parseGlyf=function(i,s){var a=e._bin,o=i._data,l=e._tabOffset(o,"glyf",i._offset)+i.loca[s];if(i.loca[s]==i.loca[s+1])return null;var c={};if(c.noc=a.readShort(o,l),l+=2,c.xMin=a.readShort(o,l),l+=2,c.yMin=a.readShort(o,l),l+=2,c.xMax=a.readShort(o,l),l+=2,c.yMax=a.readShort(o,l),l+=2,c.xMin>=c.xMax||c.yMin>=c.yMax)return null;if(c.noc>0){c.endPts=[];for(var u=0;u<c.noc;u++)c.endPts.push(a.readUshort(o,l)),l+=2;var f=a.readUshort(o,l);if(l+=2,o.length-l<f)return null;c.instructions=a.readBytes(o,l,f),l+=f;var h=c.endPts[c.noc-1]+1;for(c.flags=[],u=0;u<h;u++){var d=o[l];if(l++,c.flags.push(d),(8&d)!=0){var m=o[l];l++;for(var g=0;g<m;g++)c.flags.push(d),u++}}for(c.xs=[],u=0;u<h;u++){var p=(2&c.flags[u])!=0,_=(16&c.flags[u])!=0;p?(c.xs.push(_?o[l]:-o[l]),l++):_?c.xs.push(0):(c.xs.push(a.readShort(o,l)),l+=2)}for(c.ys=[],u=0;u<h;u++)p=(4&c.flags[u])!=0,_=(32&c.flags[u])!=0,p?(c.ys.push(_?o[l]:-o[l]),l++):_?c.ys.push(0):(c.ys.push(a.readShort(o,l)),l+=2);var M=0,y=0;for(u=0;u<h;u++)M+=c.xs[u],y+=c.ys[u],c.xs[u]=M,c.ys[u]=y}else{var v;c.parts=[];do{v=a.readUshort(o,l),l+=2;var S={m:{a:1,b:0,c:0,d:1,tx:0,ty:0},p1:-1,p2:-1};if(c.parts.push(S),S.glyphIndex=a.readUshort(o,l),l+=2,1&v){var b=a.readShort(o,l);l+=2;var E=a.readShort(o,l);l+=2}else b=a.readInt8(o,l),l++,E=a.readInt8(o,l),l++;2&v?(S.m.tx=b,S.m.ty=E):(S.p1=b,S.p2=E),8&v?(S.m.a=S.m.d=a.readF2dot14(o,l),l+=2):64&v?(S.m.a=a.readF2dot14(o,l),l+=2,S.m.d=a.readF2dot14(o,l),l+=2):128&v&&(S.m.a=a.readF2dot14(o,l),l+=2,S.m.b=a.readF2dot14(o,l),l+=2,S.m.c=a.readF2dot14(o,l),l+=2,S.m.d=a.readF2dot14(o,l),l+=2)}while(32&v);if(256&v){var x=a.readUshort(o,l);for(l+=2,c.instr=[],u=0;u<x;u++)c.instr.push(o[l]),l++}}return c},e.GDEF={},e.GDEF.parse=function(i,s,a,o){var l=s;s+=4;var c=e._bin.readUshort(i,s);return{glyphClassDef:c===0?null:e._lctf.readClassDef(i,l+c)}},e.GPOS={},e.GPOS.parse=function(i,s,a,o){return e._lctf.parse(i,s,a,o,e.GPOS.subt)},e.GPOS.subt=function(i,s,a,o){var l=e._bin,c=a,u={};if(u.fmt=l.readUshort(i,a),a+=2,s==1||s==2||s==3||s==7||s==8&&u.fmt<=2){var f=l.readUshort(i,a);a+=2,u.coverage=e._lctf.readCoverage(i,f+c)}if(s==1&&u.fmt==1){var h=l.readUshort(i,a);a+=2,h!=0&&(u.pos=e.GPOS.readValueRecord(i,a,h))}else if(s==2&&u.fmt>=1&&u.fmt<=2){h=l.readUshort(i,a),a+=2;var d=l.readUshort(i,a);a+=2;var m=e._lctf.numOfOnes(h),g=e._lctf.numOfOnes(d);if(u.fmt==1){u.pairsets=[];var p=l.readUshort(i,a);a+=2;for(var _=0;_<p;_++){var M=c+l.readUshort(i,a);a+=2;var y=l.readUshort(i,M);M+=2;for(var v=[],S=0;S<y;S++){var b=l.readUshort(i,M);M+=2,h!=0&&(A=e.GPOS.readValueRecord(i,M,h),M+=2*m),d!=0&&(U=e.GPOS.readValueRecord(i,M,d),M+=2*g),v.push({gid2:b,val1:A,val2:U})}u.pairsets.push(v)}}if(u.fmt==2){var E=l.readUshort(i,a);a+=2;var x=l.readUshort(i,a);a+=2;var w=l.readUshort(i,a);a+=2;var R=l.readUshort(i,a);for(a+=2,u.classDef1=e._lctf.readClassDef(i,c+E),u.classDef2=e._lctf.readClassDef(i,c+x),u.matrix=[],_=0;_<w;_++){var L=[];for(S=0;S<R;S++){var A=null,U=null;h!=0&&(A=e.GPOS.readValueRecord(i,a,h),a+=2*m),d!=0&&(U=e.GPOS.readValueRecord(i,a,d),a+=2*g),L.push({val1:A,val2:U})}u.matrix.push(L)}}}else if(s==4&&u.fmt==1)u.markCoverage=e._lctf.readCoverage(i,l.readUshort(i,a)+c),u.baseCoverage=e._lctf.readCoverage(i,l.readUshort(i,a+2)+c),u.markClassCount=l.readUshort(i,a+4),u.markArray=e.GPOS.readMarkArray(i,l.readUshort(i,a+6)+c),u.baseArray=e.GPOS.readBaseArray(i,l.readUshort(i,a+8)+c,u.markClassCount);else if(s==6&&u.fmt==1)u.mark1Coverage=e._lctf.readCoverage(i,l.readUshort(i,a)+c),u.mark2Coverage=e._lctf.readCoverage(i,l.readUshort(i,a+2)+c),u.markClassCount=l.readUshort(i,a+4),u.mark1Array=e.GPOS.readMarkArray(i,l.readUshort(i,a+6)+c),u.mark2Array=e.GPOS.readBaseArray(i,l.readUshort(i,a+8)+c,u.markClassCount);else{if(s==9&&u.fmt==1){var P=l.readUshort(i,a);a+=2;var I=l.readUint(i,a);if(a+=4,o.ltype==9)o.ltype=P;else if(o.ltype!=P)throw"invalid extension substitution";return e.GPOS.subt(i,o.ltype,c+I)}console.debug("unsupported GPOS table LookupType",s,"format",u.fmt)}return u},e.GPOS.readValueRecord=function(i,s,a){var o=e._bin,l=[];return l.push(1&a?o.readShort(i,s):0),s+=1&a?2:0,l.push(2&a?o.readShort(i,s):0),s+=2&a?2:0,l.push(4&a?o.readShort(i,s):0),s+=4&a?2:0,l.push(8&a?o.readShort(i,s):0),s+=8&a?2:0,l},e.GPOS.readBaseArray=function(i,s,a){var o=e._bin,l=[],c=s,u=o.readUshort(i,s);s+=2;for(var f=0;f<u;f++){for(var h=[],d=0;d<a;d++)h.push(e.GPOS.readAnchorRecord(i,c+o.readUshort(i,s))),s+=2;l.push(h)}return l},e.GPOS.readMarkArray=function(i,s){var a=e._bin,o=[],l=s,c=a.readUshort(i,s);s+=2;for(var u=0;u<c;u++){var f=e.GPOS.readAnchorRecord(i,a.readUshort(i,s+2)+l);f.markClass=a.readUshort(i,s),o.push(f),s+=4}return o},e.GPOS.readAnchorRecord=function(i,s){var a=e._bin,o={};return o.fmt=a.readUshort(i,s),o.x=a.readShort(i,s+2),o.y=a.readShort(i,s+4),o},e.GSUB={},e.GSUB.parse=function(i,s,a,o){return e._lctf.parse(i,s,a,o,e.GSUB.subt)},e.GSUB.subt=function(i,s,a,o){var l=e._bin,c=a,u={};if(u.fmt=l.readUshort(i,a),a+=2,s!=1&&s!=2&&s!=4&&s!=5&&s!=6)return null;if(s==1||s==2||s==4||s==5&&u.fmt<=2||s==6&&u.fmt<=2){var f=l.readUshort(i,a);a+=2,u.coverage=e._lctf.readCoverage(i,c+f)}if(s==1&&u.fmt>=1&&u.fmt<=2){if(u.fmt==1)u.delta=l.readShort(i,a),a+=2;else if(u.fmt==2){var h=l.readUshort(i,a);a+=2,u.newg=l.readUshorts(i,a,h),a+=2*u.newg.length}}else if(s==2&&u.fmt==1){h=l.readUshort(i,a),a+=2,u.seqs=[];for(var d=0;d<h;d++){var m=l.readUshort(i,a)+c;a+=2;var g=l.readUshort(i,m);u.seqs.push(l.readUshorts(i,m+2,g))}}else if(s==4)for(u.vals=[],h=l.readUshort(i,a),a+=2,d=0;d<h;d++){var p=l.readUshort(i,a);a+=2,u.vals.push(e.GSUB.readLigatureSet(i,c+p))}else if(s==5&&u.fmt==2){if(u.fmt==2){var _=l.readUshort(i,a);a+=2,u.cDef=e._lctf.readClassDef(i,c+_),u.scset=[];var M=l.readUshort(i,a);for(a+=2,d=0;d<M;d++){var y=l.readUshort(i,a);a+=2,u.scset.push(y==0?null:e.GSUB.readSubClassSet(i,c+y))}}}else if(s==6&&u.fmt==3){if(u.fmt==3){for(d=0;d<3;d++){h=l.readUshort(i,a),a+=2;for(var v=[],S=0;S<h;S++)v.push(e._lctf.readCoverage(i,c+l.readUshort(i,a+2*S)));a+=2*h,d==0&&(u.backCvg=v),d==1&&(u.inptCvg=v),d==2&&(u.ahedCvg=v)}h=l.readUshort(i,a),a+=2,u.lookupRec=e.GSUB.readSubstLookupRecords(i,a,h)}}else{if(s==7&&u.fmt==1){var b=l.readUshort(i,a);a+=2;var E=l.readUint(i,a);if(a+=4,o.ltype==9)o.ltype=b;else if(o.ltype!=b)throw"invalid extension substitution";return e.GSUB.subt(i,o.ltype,c+E)}console.debug("unsupported GSUB table LookupType",s,"format",u.fmt)}return u},e.GSUB.readSubClassSet=function(i,s){var a=e._bin.readUshort,o=s,l=[],c=a(i,s);s+=2;for(var u=0;u<c;u++){var f=a(i,s);s+=2,l.push(e.GSUB.readSubClassRule(i,o+f))}return l},e.GSUB.readSubClassRule=function(i,s){var a=e._bin.readUshort,o={},l=a(i,s),c=a(i,s+=2);s+=2,o.input=[];for(var u=0;u<l-1;u++)o.input.push(a(i,s)),s+=2;return o.substLookupRecords=e.GSUB.readSubstLookupRecords(i,s,c),o},e.GSUB.readSubstLookupRecords=function(i,s,a){for(var o=e._bin.readUshort,l=[],c=0;c<a;c++)l.push(o(i,s),o(i,s+2)),s+=4;return l},e.GSUB.readChainSubClassSet=function(i,s){var a=e._bin,o=s,l=[],c=a.readUshort(i,s);s+=2;for(var u=0;u<c;u++){var f=a.readUshort(i,s);s+=2,l.push(e.GSUB.readChainSubClassRule(i,o+f))}return l},e.GSUB.readChainSubClassRule=function(i,s){for(var a=e._bin,o={},l=["backtrack","input","lookahead"],c=0;c<l.length;c++){var u=a.readUshort(i,s);s+=2,c==1&&u--,o[l[c]]=a.readUshorts(i,s,u),s+=2*o[l[c]].length}return u=a.readUshort(i,s),s+=2,o.subst=a.readUshorts(i,s,2*u),s+=2*o.subst.length,o},e.GSUB.readLigatureSet=function(i,s){var a=e._bin,o=s,l=[],c=a.readUshort(i,s);s+=2;for(var u=0;u<c;u++){var f=a.readUshort(i,s);s+=2,l.push(e.GSUB.readLigature(i,o+f))}return l},e.GSUB.readLigature=function(i,s){var a=e._bin,o={chain:[]};o.nglyph=a.readUshort(i,s),s+=2;var l=a.readUshort(i,s);s+=2;for(var c=0;c<l-1;c++)o.chain.push(a.readUshort(i,s)),s+=2;return o},e.head={},e.head.parse=function(i,s,a){var o=e._bin,l={};return o.readFixed(i,s),s+=4,l.fontRevision=o.readFixed(i,s),s+=4,o.readUint(i,s),s+=4,o.readUint(i,s),s+=4,l.flags=o.readUshort(i,s),s+=2,l.unitsPerEm=o.readUshort(i,s),s+=2,l.created=o.readUint64(i,s),s+=8,l.modified=o.readUint64(i,s),s+=8,l.xMin=o.readShort(i,s),s+=2,l.yMin=o.readShort(i,s),s+=2,l.xMax=o.readShort(i,s),s+=2,l.yMax=o.readShort(i,s),s+=2,l.macStyle=o.readUshort(i,s),s+=2,l.lowestRecPPEM=o.readUshort(i,s),s+=2,l.fontDirectionHint=o.readShort(i,s),s+=2,l.indexToLocFormat=o.readShort(i,s),s+=2,l.glyphDataFormat=o.readShort(i,s),s+=2,l},e.hhea={},e.hhea.parse=function(i,s,a){var o=e._bin,l={};return o.readFixed(i,s),s+=4,l.ascender=o.readShort(i,s),s+=2,l.descender=o.readShort(i,s),s+=2,l.lineGap=o.readShort(i,s),s+=2,l.advanceWidthMax=o.readUshort(i,s),s+=2,l.minLeftSideBearing=o.readShort(i,s),s+=2,l.minRightSideBearing=o.readShort(i,s),s+=2,l.xMaxExtent=o.readShort(i,s),s+=2,l.caretSlopeRise=o.readShort(i,s),s+=2,l.caretSlopeRun=o.readShort(i,s),s+=2,l.caretOffset=o.readShort(i,s),s+=2,s+=8,l.metricDataFormat=o.readShort(i,s),s+=2,l.numberOfHMetrics=o.readUshort(i,s),s+=2,l},e.hmtx={},e.hmtx.parse=function(i,s,a,o){for(var l=e._bin,c={aWidth:[],lsBearing:[]},u=0,f=0,h=0;h<o.maxp.numGlyphs;h++)h<o.hhea.numberOfHMetrics&&(u=l.readUshort(i,s),s+=2,f=l.readShort(i,s),s+=2),c.aWidth.push(u),c.lsBearing.push(f);return c},e.kern={},e.kern.parse=function(i,s,a,o){var l=e._bin,c=l.readUshort(i,s);if(s+=2,c==1)return e.kern.parseV1(i,s-2,a,o);var u=l.readUshort(i,s);s+=2;for(var f={glyph1:[],rval:[]},h=0;h<u;h++){s+=2,a=l.readUshort(i,s),s+=2;var d=l.readUshort(i,s);s+=2;var m=d>>>8;if((m&=15)!=0)throw"unknown kern table format: "+m;s=e.kern.readFormat0(i,s,f)}return f},e.kern.parseV1=function(i,s,a,o){var l=e._bin;l.readFixed(i,s),s+=4;var c=l.readUint(i,s);s+=4;for(var u={glyph1:[],rval:[]},f=0;f<c;f++){l.readUint(i,s),s+=4;var h=l.readUshort(i,s);s+=2,l.readUshort(i,s),s+=2;var d=h>>>8;if((d&=15)!=0)throw"unknown kern table format: "+d;s=e.kern.readFormat0(i,s,u)}return u},e.kern.readFormat0=function(i,s,a){var o=e._bin,l=-1,c=o.readUshort(i,s);s+=2,o.readUshort(i,s),s+=2,o.readUshort(i,s),s+=2,o.readUshort(i,s),s+=2;for(var u=0;u<c;u++){var f=o.readUshort(i,s);s+=2;var h=o.readUshort(i,s);s+=2;var d=o.readShort(i,s);s+=2,f!=l&&(a.glyph1.push(f),a.rval.push({glyph2:[],vals:[]}));var m=a.rval[a.rval.length-1];m.glyph2.push(h),m.vals.push(d),l=f}return s},e.loca={},e.loca.parse=function(i,s,a,o){var l=e._bin,c=[],u=o.head.indexToLocFormat,f=o.maxp.numGlyphs+1;if(u==0)for(var h=0;h<f;h++)c.push(l.readUshort(i,s+(h<<1))<<1);if(u==1)for(h=0;h<f;h++)c.push(l.readUint(i,s+(h<<2)));return c},e.maxp={},e.maxp.parse=function(i,s,a){var o=e._bin,l={},c=o.readUint(i,s);return s+=4,l.numGlyphs=o.readUshort(i,s),s+=2,c==65536&&(l.maxPoints=o.readUshort(i,s),s+=2,l.maxContours=o.readUshort(i,s),s+=2,l.maxCompositePoints=o.readUshort(i,s),s+=2,l.maxCompositeContours=o.readUshort(i,s),s+=2,l.maxZones=o.readUshort(i,s),s+=2,l.maxTwilightPoints=o.readUshort(i,s),s+=2,l.maxStorage=o.readUshort(i,s),s+=2,l.maxFunctionDefs=o.readUshort(i,s),s+=2,l.maxInstructionDefs=o.readUshort(i,s),s+=2,l.maxStackElements=o.readUshort(i,s),s+=2,l.maxSizeOfInstructions=o.readUshort(i,s),s+=2,l.maxComponentElements=o.readUshort(i,s),s+=2,l.maxComponentDepth=o.readUshort(i,s),s+=2),l},e.name={},e.name.parse=function(i,s,a){var o=e._bin,l={};o.readUshort(i,s),s+=2;var c=o.readUshort(i,s);s+=2,o.readUshort(i,s);for(var u,f=["copyright","fontFamily","fontSubfamily","ID","fullName","version","postScriptName","trademark","manufacturer","designer","description","urlVendor","urlDesigner","licence","licenceURL","---","typoFamilyName","typoSubfamilyName","compatibleFull","sampleText","postScriptCID","wwsFamilyName","wwsSubfamilyName","lightPalette","darkPalette"],h=s+=2,d=0;d<c;d++){var m=o.readUshort(i,s);s+=2;var g=o.readUshort(i,s);s+=2;var p=o.readUshort(i,s);s+=2;var _=o.readUshort(i,s);s+=2;var M=o.readUshort(i,s);s+=2;var y=o.readUshort(i,s);s+=2;var v,S=f[_],b=h+12*c+y;if(m==0)v=o.readUnicode(i,b,M/2);else if(m==3&&g==0)v=o.readUnicode(i,b,M/2);else if(g==0)v=o.readASCII(i,b,M);else if(g==1)v=o.readUnicode(i,b,M/2);else if(g==3)v=o.readUnicode(i,b,M/2);else{if(m!=1)throw"unknown encoding "+g+", platformID: "+m;v=o.readASCII(i,b,M),console.debug("reading unknown MAC encoding "+g+" as ASCII")}var E="p"+m+","+p.toString(16);l[E]==null&&(l[E]={}),l[E][S!==void 0?S:_]=v,l[E]._lang=p}for(var x in l)if(l[x].postScriptName!=null&&l[x]._lang==1033)return l[x];for(var x in l)if(l[x].postScriptName!=null&&l[x]._lang==0)return l[x];for(var x in l)if(l[x].postScriptName!=null&&l[x]._lang==3084)return l[x];for(var x in l)if(l[x].postScriptName!=null)return l[x];for(var x in l){u=x;break}return console.debug("returning name table with languageID "+l[u]._lang),l[u]},e["OS/2"]={},e["OS/2"].parse=function(i,s,a){var o=e._bin.readUshort(i,s);s+=2;var l={};if(o==0)e["OS/2"].version0(i,s,l);else if(o==1)e["OS/2"].version1(i,s,l);else if(o==2||o==3||o==4)e["OS/2"].version2(i,s,l);else{if(o!=5)throw"unknown OS/2 table version: "+o;e["OS/2"].version5(i,s,l)}return l},e["OS/2"].version0=function(i,s,a){var o=e._bin;return a.xAvgCharWidth=o.readShort(i,s),s+=2,a.usWeightClass=o.readUshort(i,s),s+=2,a.usWidthClass=o.readUshort(i,s),s+=2,a.fsType=o.readUshort(i,s),s+=2,a.ySubscriptXSize=o.readShort(i,s),s+=2,a.ySubscriptYSize=o.readShort(i,s),s+=2,a.ySubscriptXOffset=o.readShort(i,s),s+=2,a.ySubscriptYOffset=o.readShort(i,s),s+=2,a.ySuperscriptXSize=o.readShort(i,s),s+=2,a.ySuperscriptYSize=o.readShort(i,s),s+=2,a.ySuperscriptXOffset=o.readShort(i,s),s+=2,a.ySuperscriptYOffset=o.readShort(i,s),s+=2,a.yStrikeoutSize=o.readShort(i,s),s+=2,a.yStrikeoutPosition=o.readShort(i,s),s+=2,a.sFamilyClass=o.readShort(i,s),s+=2,a.panose=o.readBytes(i,s,10),s+=10,a.ulUnicodeRange1=o.readUint(i,s),s+=4,a.ulUnicodeRange2=o.readUint(i,s),s+=4,a.ulUnicodeRange3=o.readUint(i,s),s+=4,a.ulUnicodeRange4=o.readUint(i,s),s+=4,a.achVendID=[o.readInt8(i,s),o.readInt8(i,s+1),o.readInt8(i,s+2),o.readInt8(i,s+3)],s+=4,a.fsSelection=o.readUshort(i,s),s+=2,a.usFirstCharIndex=o.readUshort(i,s),s+=2,a.usLastCharIndex=o.readUshort(i,s),s+=2,a.sTypoAscender=o.readShort(i,s),s+=2,a.sTypoDescender=o.readShort(i,s),s+=2,a.sTypoLineGap=o.readShort(i,s),s+=2,a.usWinAscent=o.readUshort(i,s),s+=2,a.usWinDescent=o.readUshort(i,s),s+=2},e["OS/2"].version1=function(i,s,a){var o=e._bin;return s=e["OS/2"].version0(i,s,a),a.ulCodePageRange1=o.readUint(i,s),s+=4,a.ulCodePageRange2=o.readUint(i,s),s+=4},e["OS/2"].version2=function(i,s,a){var o=e._bin;return s=e["OS/2"].version1(i,s,a),a.sxHeight=o.readShort(i,s),s+=2,a.sCapHeight=o.readShort(i,s),s+=2,a.usDefault=o.readUshort(i,s),s+=2,a.usBreak=o.readUshort(i,s),s+=2,a.usMaxContext=o.readUshort(i,s),s+=2},e["OS/2"].version5=function(i,s,a){var o=e._bin;return s=e["OS/2"].version2(i,s,a),a.usLowerOpticalPointSize=o.readUshort(i,s),s+=2,a.usUpperOpticalPointSize=o.readUshort(i,s),s+=2},e.post={},e.post.parse=function(i,s,a){var o=e._bin,l={};return l.version=o.readFixed(i,s),s+=4,l.italicAngle=o.readFixed(i,s),s+=4,l.underlinePosition=o.readShort(i,s),s+=2,l.underlineThickness=o.readShort(i,s),s+=2,l},e==null&&(e={}),e.U==null&&(e.U={}),e.U.codeToGlyph=function(i,s){var a=i.cmap,o=-1;if(a.p0e4!=null?o=a.p0e4:a.p3e1!=null?o=a.p3e1:a.p1e0!=null?o=a.p1e0:a.p0e3!=null&&(o=a.p0e3),o==-1)throw"no familiar platform and encoding!";var l=a.tables[o];if(l.format==0)return s>=l.map.length?0:l.map[s];if(l.format==4){for(var c=-1,u=0;u<l.endCount.length;u++)if(s<=l.endCount[u]){c=u;break}return c==-1||l.startCount[c]>s?0:65535&(l.idRangeOffset[c]!=0?l.glyphIdArray[s-l.startCount[c]+(l.idRangeOffset[c]>>1)-(l.idRangeOffset.length-c)]:s+l.idDelta[c])}if(l.format==12){if(s>l.groups[l.groups.length-1][1])return 0;for(u=0;u<l.groups.length;u++){var f=l.groups[u];if(f[0]<=s&&s<=f[1])return f[2]+(s-f[0])}return 0}throw"unknown cmap table format "+l.format},e.U.glyphToPath=function(i,s){var a={cmds:[],crds:[]};if(i.SVG&&i.SVG.entries[s]){var o=i.SVG.entries[s];return o==null?a:(typeof o=="string"&&(o=e.SVG.toPath(o),i.SVG.entries[s]=o),o)}if(i.CFF){var l={x:0,y:0,stack:[],nStems:0,haveWidth:!1,width:i.CFF.Private?i.CFF.Private.defaultWidthX:0,open:!1},c=i.CFF,u=i.CFF.Private;if(c.ROS){for(var f=0;c.FDSelect[f+2]<=s;)f+=2;u=c.FDArray[c.FDSelect[f+1]].Private}e.U._drawCFF(i.CFF.CharStrings[s],l,c,u,a)}else i.glyf&&e.U._drawGlyf(s,i,a);return a},e.U._drawGlyf=function(i,s,a){var o=s.glyf[i];o==null&&(o=s.glyf[i]=e.glyf._parseGlyf(s,i)),o!=null&&(o.noc>-1?e.U._simpleGlyph(o,a):e.U._compoGlyph(o,s,a))},e.U._simpleGlyph=function(i,s){for(var a=0;a<i.noc;a++){for(var o=a==0?0:i.endPts[a-1]+1,l=i.endPts[a],c=o;c<=l;c++){var u=c==o?l:c-1,f=c==l?o:c+1,h=1&i.flags[c],d=1&i.flags[u],m=1&i.flags[f],g=i.xs[c],p=i.ys[c];if(c==o)if(h){if(!d){e.U.P.moveTo(s,g,p);continue}e.U.P.moveTo(s,i.xs[u],i.ys[u])}else d?e.U.P.moveTo(s,i.xs[u],i.ys[u]):e.U.P.moveTo(s,(i.xs[u]+g)/2,(i.ys[u]+p)/2);h?d&&e.U.P.lineTo(s,g,p):m?e.U.P.qcurveTo(s,g,p,i.xs[f],i.ys[f]):e.U.P.qcurveTo(s,g,p,(g+i.xs[f])/2,(p+i.ys[f])/2)}e.U.P.closePath(s)}},e.U._compoGlyph=function(i,s,a){for(var o=0;o<i.parts.length;o++){var l={cmds:[],crds:[]},c=i.parts[o];e.U._drawGlyf(c.glyphIndex,s,l);for(var u=c.m,f=0;f<l.crds.length;f+=2){var h=l.crds[f],d=l.crds[f+1];a.crds.push(h*u.a+d*u.b+u.tx),a.crds.push(h*u.c+d*u.d+u.ty)}for(f=0;f<l.cmds.length;f++)a.cmds.push(l.cmds[f])}},e.U._getGlyphClass=function(i,s){var a=e._lctf.getInterval(s,i);return a==-1?0:s[a+2]},e.U._applySubs=function(i,s,a,o){for(var l=i.length-s-1,c=0;c<a.tabs.length;c++)if(a.tabs[c]!=null){var u,f=a.tabs[c];if(!f.coverage||(u=e._lctf.coverageIndex(f.coverage,i[s]))!=-1){if(a.ltype==1)i[s],f.fmt==1?i[s]=i[s]+f.delta:i[s]=f.newg[u];else if(a.ltype==4)for(var h=f.vals[u],d=0;d<h.length;d++){var m=h[d],g=m.chain.length;if(!(g>l)){for(var p=!0,_=0,M=0;M<g;M++){for(;i[s+_+(1+M)]==-1;)_++;m.chain[M]!=i[s+_+(1+M)]&&(p=!1)}if(p){for(i[s]=m.nglyph,M=0;M<g+_;M++)i[s+M+1]=-1;break}}}else if(a.ltype==5&&f.fmt==2)for(var y=e._lctf.getInterval(f.cDef,i[s]),v=f.cDef[y+2],S=f.scset[v],b=0;b<S.length;b++){var E=S[b],x=E.input;if(!(x.length>l)){for(p=!0,M=0;M<x.length;M++){var w=e._lctf.getInterval(f.cDef,i[s+1+M]);if(y==-1&&f.cDef[w+2]!=x[M]){p=!1;break}}if(p){var R=E.substLookupRecords;for(d=0;d<R.length;d+=2)R[d],R[d+1]}}}else if(a.ltype==6&&f.fmt==3){if(!e.U._glsCovered(i,f.backCvg,s-f.backCvg.length)||!e.U._glsCovered(i,f.inptCvg,s)||!e.U._glsCovered(i,f.ahedCvg,s+f.inptCvg.length))continue;var L=f.lookupRec;for(b=0;b<L.length;b+=2){y=L[b];var A=o[L[b+1]];e.U._applySubs(i,s+y,A,o)}}}}},e.U._glsCovered=function(i,s,a){for(var o=0;o<s.length;o++)if(e._lctf.coverageIndex(s[o],i[a+o])==-1)return!1;return!0},e.U.glyphsToPath=function(i,s,a){for(var o={cmds:[],crds:[]},l=0,c=0;c<s.length;c++){var u=s[c];if(u!=-1){for(var f=c<s.length-1&&s[c+1]!=-1?s[c+1]:0,h=e.U.glyphToPath(i,u),d=0;d<h.crds.length;d+=2)o.crds.push(h.crds[d]+l),o.crds.push(h.crds[d+1]);for(a&&o.cmds.push(a),d=0;d<h.cmds.length;d++)o.cmds.push(h.cmds[d]);a&&o.cmds.push("X"),l+=i.hmtx.aWidth[u],c<s.length-1&&(l+=e.U.getPairAdjustment(i,u,f))}}return o},e.U.P={},e.U.P.moveTo=function(i,s,a){i.cmds.push("M"),i.crds.push(s,a)},e.U.P.lineTo=function(i,s,a){i.cmds.push("L"),i.crds.push(s,a)},e.U.P.curveTo=function(i,s,a,o,l,c,u){i.cmds.push("C"),i.crds.push(s,a,o,l,c,u)},e.U.P.qcurveTo=function(i,s,a,o,l){i.cmds.push("Q"),i.crds.push(s,a,o,l)},e.U.P.closePath=function(i){i.cmds.push("Z")},e.U._drawCFF=function(i,s,a,o,l){for(var c=s.stack,u=s.nStems,f=s.haveWidth,h=s.width,d=s.open,m=0,g=s.x,p=s.y,_=0,M=0,y=0,v=0,S=0,b=0,E=0,x=0,w=0,R=0,L={val:0,size:0};m<i.length;){e.CFF.getCharString(i,m,L);var A=L.val;if(m+=L.size,A=="o1"||A=="o18")c.length%2!=0&&!f&&(h=c.shift()+o.nominalWidthX),u+=c.length>>1,c.length=0,f=!0;else if(A=="o3"||A=="o23")c.length%2!=0&&!f&&(h=c.shift()+o.nominalWidthX),u+=c.length>>1,c.length=0,f=!0;else if(A=="o4")c.length>1&&!f&&(h=c.shift()+o.nominalWidthX,f=!0),d&&e.U.P.closePath(l),p+=c.pop(),e.U.P.moveTo(l,g,p),d=!0;else if(A=="o5")for(;c.length>0;)g+=c.shift(),p+=c.shift(),e.U.P.lineTo(l,g,p);else if(A=="o6"||A=="o7")for(var U=c.length,P=A=="o6",I=0;I<U;I++){var F=c.shift();P?g+=F:p+=F,P=!P,e.U.P.lineTo(l,g,p)}else if(A=="o8"||A=="o24"){U=c.length;for(var O=0;O+6<=U;)_=g+c.shift(),M=p+c.shift(),y=_+c.shift(),v=M+c.shift(),g=y+c.shift(),p=v+c.shift(),e.U.P.curveTo(l,_,M,y,v,g,p),O+=6;A=="o24"&&(g+=c.shift(),p+=c.shift(),e.U.P.lineTo(l,g,p))}else{if(A=="o11")break;if(A=="o1234"||A=="o1235"||A=="o1236"||A=="o1237")A=="o1234"&&(M=p,y=(_=g+c.shift())+c.shift(),R=v=M+c.shift(),b=v,x=p,g=(E=(S=(w=y+c.shift())+c.shift())+c.shift())+c.shift(),e.U.P.curveTo(l,_,M,y,v,w,R),e.U.P.curveTo(l,S,b,E,x,g,p)),A=="o1235"&&(_=g+c.shift(),M=p+c.shift(),y=_+c.shift(),v=M+c.shift(),w=y+c.shift(),R=v+c.shift(),S=w+c.shift(),b=R+c.shift(),E=S+c.shift(),x=b+c.shift(),g=E+c.shift(),p=x+c.shift(),c.shift(),e.U.P.curveTo(l,_,M,y,v,w,R),e.U.P.curveTo(l,S,b,E,x,g,p)),A=="o1236"&&(_=g+c.shift(),M=p+c.shift(),y=_+c.shift(),R=v=M+c.shift(),b=v,E=(S=(w=y+c.shift())+c.shift())+c.shift(),x=b+c.shift(),g=E+c.shift(),e.U.P.curveTo(l,_,M,y,v,w,R),e.U.P.curveTo(l,S,b,E,x,g,p)),A=="o1237"&&(_=g+c.shift(),M=p+c.shift(),y=_+c.shift(),v=M+c.shift(),w=y+c.shift(),R=v+c.shift(),S=w+c.shift(),b=R+c.shift(),E=S+c.shift(),x=b+c.shift(),Math.abs(E-g)>Math.abs(x-p)?g=E+c.shift():p=x+c.shift(),e.U.P.curveTo(l,_,M,y,v,w,R),e.U.P.curveTo(l,S,b,E,x,g,p));else if(A=="o14"){if(c.length>0&&!f&&(h=c.shift()+a.nominalWidthX,f=!0),c.length==4){var q=c.shift(),z=c.shift(),k=c.shift(),N=c.shift(),G=e.CFF.glyphBySE(a,k),K=e.CFF.glyphBySE(a,N);e.U._drawCFF(a.CharStrings[G],s,a,o,l),s.x=q,s.y=z,e.U._drawCFF(a.CharStrings[K],s,a,o,l)}d&&(e.U.P.closePath(l),d=!1)}else if(A=="o19"||A=="o20")c.length%2!=0&&!f&&(h=c.shift()+o.nominalWidthX),u+=c.length>>1,c.length=0,f=!0,m+=u+7>>3;else if(A=="o21")c.length>2&&!f&&(h=c.shift()+o.nominalWidthX,f=!0),p+=c.pop(),g+=c.pop(),d&&e.U.P.closePath(l),e.U.P.moveTo(l,g,p),d=!0;else if(A=="o22")c.length>1&&!f&&(h=c.shift()+o.nominalWidthX,f=!0),g+=c.pop(),d&&e.U.P.closePath(l),e.U.P.moveTo(l,g,p),d=!0;else if(A=="o25"){for(;c.length>6;)g+=c.shift(),p+=c.shift(),e.U.P.lineTo(l,g,p);_=g+c.shift(),M=p+c.shift(),y=_+c.shift(),v=M+c.shift(),g=y+c.shift(),p=v+c.shift(),e.U.P.curveTo(l,_,M,y,v,g,p)}else if(A=="o26")for(c.length%2&&(g+=c.shift());c.length>0;)_=g,M=p+c.shift(),g=y=_+c.shift(),p=(v=M+c.shift())+c.shift(),e.U.P.curveTo(l,_,M,y,v,g,p);else if(A=="o27")for(c.length%2&&(p+=c.shift());c.length>0;)M=p,y=(_=g+c.shift())+c.shift(),v=M+c.shift(),g=y+c.shift(),p=v,e.U.P.curveTo(l,_,M,y,v,g,p);else if(A=="o10"||A=="o29"){var J=A=="o10"?o:a;if(c.length==0)console.debug("error: empty stack");else{var j=c.pop(),V=J.Subrs[j+J.Bias];s.x=g,s.y=p,s.nStems=u,s.haveWidth=f,s.width=h,s.open=d,e.U._drawCFF(V,s,a,o,l),g=s.x,p=s.y,u=s.nStems,f=s.haveWidth,h=s.width,d=s.open}}else if(A=="o30"||A=="o31"){var Y=c.length,Z=(O=0,A=="o31");for(O+=Y-(U=-3&Y);O<U;)Z?(M=p,y=(_=g+c.shift())+c.shift(),p=(v=M+c.shift())+c.shift(),U-O==5?(g=y+c.shift(),O++):g=y,Z=!1):(_=g,M=p+c.shift(),y=_+c.shift(),v=M+c.shift(),g=y+c.shift(),U-O==5?(p=v+c.shift(),O++):p=v,Z=!0),e.U.P.curveTo(l,_,M,y,v,g,p),O+=4}else{if((A+"").charAt(0)=="o")throw console.debug("Unknown operation: "+A,i),A;c.push(A)}}}s.x=g,s.y=p,s.nStems=u,s.haveWidth=f,s.width=h,s.open=d};var t=e,r={Typr:t};return n.Typr=t,n.default=r,Object.defineProperty(n,"__esModule",{value:!0}),n})({}).Typr}/*!
Custom bundle of woff2otf (https://github.com/arty-name/woff2otf) with fflate
(https://github.com/101arrowz/fflate) for use in Troika text rendering. 
Original licenses apply: 
- fflate: https://github.com/101arrowz/fflate/blob/master/LICENSE (MIT)
- woff2otf.js: https://github.com/arty-name/woff2otf/blob/master/woff2otf.js (Apache2)
*/function Mb(){return(function(n){var e=Uint8Array,t=Uint16Array,r=Uint32Array,i=new e([0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0,0,0,0]),s=new e([0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13,0,0]),a=new e([16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15]),o=function(A,U){for(var P=new t(31),I=0;I<31;++I)P[I]=U+=1<<A[I-1];var F=new r(P[30]);for(I=1;I<30;++I)for(var O=P[I];O<P[I+1];++O)F[O]=O-P[I]<<5|I;return[P,F]},l=o(i,2),c=l[0],u=l[1];c[28]=258,u[258]=28;for(var f=o(s,0)[0],h=new t(32768),d=0;d<32768;++d){var m=(43690&d)>>>1|(21845&d)<<1;m=(61680&(m=(52428&m)>>>2|(13107&m)<<2))>>>4|(3855&m)<<4,h[d]=((65280&m)>>>8|(255&m)<<8)>>>1}var g=function(A,U,P){for(var I=A.length,F=0,O=new t(U);F<I;++F)++O[A[F]-1];var q,z=new t(U);for(F=0;F<U;++F)z[F]=z[F-1]+O[F-1]<<1;{q=new t(1<<U);var k=15-U;for(F=0;F<I;++F)if(A[F])for(var N=F<<4|A[F],G=U-A[F],K=z[A[F]-1]++<<G,J=K|(1<<G)-1;K<=J;++K)q[h[K]>>>k]=N}return q},p=new e(288);for(d=0;d<144;++d)p[d]=8;for(d=144;d<256;++d)p[d]=9;for(d=256;d<280;++d)p[d]=7;for(d=280;d<288;++d)p[d]=8;var _=new e(32);for(d=0;d<32;++d)_[d]=5;var M=g(p,9),y=g(_,5),v=function(A){for(var U=A[0],P=1;P<A.length;++P)A[P]>U&&(U=A[P]);return U},S=function(A,U,P){var I=U/8|0;return(A[I]|A[I+1]<<8)>>(7&U)&P},b=function(A,U){var P=U/8|0;return(A[P]|A[P+1]<<8|A[P+2]<<16)>>(7&U)},E=["unexpected EOF","invalid block type","invalid length/literal","invalid distance","stream finished","no stream handler",,"no callback","invalid UTF-8 data","extra field too long","date not in range 1980-2099","filename too long","stream finishing","invalid zip data"],x=function(A,U,P){var I=new Error(U||E[A]);if(I.code=A,Error.captureStackTrace&&Error.captureStackTrace(I,x),!P)throw I;return I},w=function(A,U,P){var I=A.length;if(!I||P&&!P.l&&I<5)return U||new e(0);var F=!U||P,O=!P||P.i;P||(P={}),U||(U=new e(3*I));var q,z=function(he){var Re=U.length;if(he>Re){var ve=new e(Math.max(2*Re,he));ve.set(U),U=ve}},k=P.f||0,N=P.p||0,G=P.b||0,K=P.l,J=P.d,j=P.m,V=P.n,Y=8*I;do{if(!K){P.f=k=S(A,N,1);var Z=S(A,N+1,3);if(N+=3,!Z){var fe=A[(B=((q=N)/8|0)+(7&q&&1)+4)-4]|A[B-3]<<8,_e=B+fe;if(_e>I){O&&x(0);break}F&&z(G+fe),U.set(A.subarray(B,_e),G),P.b=G+=fe,P.p=N=8*_e;continue}if(Z==1)K=M,J=y,j=9,V=5;else if(Z==2){var le=S(A,N,31)+257,de=S(A,N+10,15)+4,Fe=le+S(A,N+5,31)+1;N+=14;for(var Ne=new e(Fe),Ae=new e(19),be=0;be<de;++be)Ae[a[be]]=S(A,N+3*be,7);N+=3*de;var ze=v(Ae),ge=(1<<ze)-1,ke=g(Ae,ze);for(be=0;be<Fe;){var B,ue=ke[S(A,N,ge)];if(N+=15&ue,(B=ue>>>4)<16)Ne[be++]=B;else{var De=0,ye=0;for(B==16?(ye=3+S(A,N,3),N+=2,De=Ne[be-1]):B==17?(ye=3+S(A,N,7),N+=3):B==18&&(ye=11+S(A,N,127),N+=7);ye--;)Ne[be++]=De}}var ce=Ne.subarray(0,le),Te=Ne.subarray(le);j=v(ce),V=v(Te),K=g(ce,j),J=g(Te,V)}else x(1);if(N>Y){O&&x(0);break}}F&&z(G+131072);for(var D=(1<<j)-1,T=(1<<V)-1,H=N;;H=N){var Q=(De=K[b(A,N)&D])>>>4;if((N+=15&De)>Y){O&&x(0);break}if(De||x(2),Q<256)U[G++]=Q;else{if(Q==256){H=N,K=null;break}var oe=Q-254;if(Q>264){var me=i[be=Q-257];oe=S(A,N,(1<<me)-1)+c[be],N+=me}var Me=J[b(A,N)&T],ee=Me>>>4;if(Me||x(3),N+=15&Me,Te=f[ee],ee>3&&(me=s[ee],Te+=b(A,N)&(1<<me)-1,N+=me),N>Y){O&&x(0);break}F&&z(G+131072);for(var re=G+oe;G<re;G+=4)U[G]=U[G-Te],U[G+1]=U[G+1-Te],U[G+2]=U[G+2-Te],U[G+3]=U[G+3-Te];G=re}}P.l=K,P.p=H,P.b=G,K&&(k=1,P.m=j,P.d=J,P.n=V)}while(!k);return G==U.length?U:(function(he,Re,ve){(ve==null||ve>he.length)&&(ve=he.length);var Se=new(he instanceof t?t:he instanceof r?r:e)(ve-Re);return Se.set(he.subarray(Re,ve)),Se})(U,0,G)},R=new e(0),L=typeof TextDecoder<"u"&&new TextDecoder;try{L.decode(R,{stream:!0})}catch{}return n.convert_streams=function(A){var U=new DataView(A),P=0;function I(){var le=U.getUint16(P);return P+=2,le}function F(){var le=U.getUint32(P);return P+=4,le}function O(le){fe.setUint16(_e,le),_e+=2}function q(le){fe.setUint32(_e,le),_e+=4}for(var z={signature:F(),flavor:F(),length:F(),numTables:I(),reserved:I(),totalSfntSize:F(),majorVersion:I(),minorVersion:I(),metaOffset:F(),metaLength:F(),metaOrigLength:F(),privOffset:F(),privLength:F()},k=0;Math.pow(2,k)<=z.numTables;)k++;k--;for(var N=16*Math.pow(2,k),G=16*z.numTables-N,K=12,J=[],j=0;j<z.numTables;j++)J.push({tag:F(),offset:F(),compLength:F(),origLength:F(),origChecksum:F()}),K+=16;var V,Y=new Uint8Array(12+16*J.length+J.reduce((function(le,de){return le+de.origLength+4}),0)),Z=Y.buffer,fe=new DataView(Z),_e=0;return q(z.flavor),O(z.numTables),O(N),O(k),O(G),J.forEach((function(le){q(le.tag),q(le.origChecksum),q(K),q(le.origLength),le.outOffset=K,(K+=le.origLength)%4!=0&&(K+=4-K%4)})),J.forEach((function(le){var de,Fe=A.slice(le.offset,le.offset+le.compLength);if(le.compLength!=le.origLength){var Ne=new Uint8Array(le.origLength);de=new Uint8Array(Fe,2),w(de,Ne)}else Ne=new Uint8Array(Fe);Y.set(Ne,le.outOffset);var Ae=0;(K=le.outOffset+le.origLength)%4!=0&&(Ae=4-K%4),Y.set(new Uint8Array(Ae).buffer,le.outOffset+le.origLength),V=K+Ae})),Z.slice(0,V)},Object.defineProperty(n,"__esModule",{value:!0}),n})({}).convert_streams}function Sb(n,e){const t={M:2,L:2,Q:4,C:6,Z:0},r={C:"18g,ca,368,1kz",D:"17k,6,2,2+4,5+c,2+6,2+1,10+1,9+f,j+11,2+1,a,2,2+1,15+2,3,j+2,6+3,2+8,2,2,2+1,w+a,4+e,3+3,2,3+2,3+5,23+w,2f+4,3,2+9,2,b,2+3,3,1k+9,6+1,3+1,2+2,2+d,30g,p+y,1,1+1g,f+x,2,sd2+1d,jf3+4,f+3,2+4,2+2,b+3,42,2,4+2,2+1,2,3,t+1,9f+w,2,el+2,2+g,d+2,2l,2+1,5,3+1,2+1,2,3,6,16wm+1v",R:"17m+3,2,2,6+3,m,15+2,2+2,h+h,13,3+8,2,2,3+1,2,p+1,x,5+4,5,a,2,2,3,u,c+2,g+1,5,2+1,4+1,5j,6+1,2,b,2+2,f,2+1,1s+2,2,3+1,7,1ez0,2,2+1,4+4,b,4,3,b,42,2+2,4,3,2+1,2,o+3,ae,ep,x,2o+2,3+1,3,5+1,6",L:"x9u,jff,a,fd,jv",T:"4t,gj+33,7o+4,1+1,7c+18,2,2+1,2+1,2,21+a,2,1b+k,h,2u+6,3+5,3+1,2+3,y,2,v+q,2k+a,1n+8,a,p+3,2+8,2+2,2+4,18+2,3c+e,2+v,1k,2,5+7,5,4+6,b+1,u,1n,5+3,9,l+1,r,3+1,1m,5+1,5+1,3+2,4,v+1,4,c+1,1m,5+4,2+1,5,l+1,n+5,2,1n,3,2+3,9,8+1,c+1,v,1q,d,1f,4,1m+2,6+2,2+3,8+1,c+1,u,1n,3,7,6+1,l+1,t+1,1m+1,5+3,9,l+1,u,21,8+2,2,2j,3+6,d+7,2r,3+8,c+5,23+1,s,2,2,1k+d,2+4,2+1,6+a,2+z,a,2v+3,2+5,2+1,3+1,q+1,5+2,h+3,e,3+1,7,g,jk+2,qb+2,u+2,u+1,v+1,1t+1,2+6,9,3+a,a,1a+2,3c+1,z,3b+2,5+1,a,7+2,64+1,3,1n,2+6,2,2,3+7,7+9,3,1d+d,1,1+1,1s+3,1d,2+4,2,6,15+8,d+1,x+3,3+1,2+2,1l,2+1,4,2+2,1n+7,3+1,49+2,2+c,2+6,5,7,4+1,5j+1l,2+4,ek,3+1,r+4,1e+4,6+5,2p+c,1+3,1,1+2,1+b,2db+2,3y,2p+v,ff+3,30+1,n9x,1+2,2+9,x+1,29+1,7l,4,5,q+1,6,48+1,r+h,e,13+7,q+a,1b+2,1d,3+3,3+1,14,1w+5,3+1,3+1,d,9,1c,1g,2+2,3+1,6+1,2,17+1,9,6n,3,5,fn5,ki+f,h+f,5s,6y+2,ea,6b,46+4,1af+2,2+1,6+3,15+2,5,4m+1,fy+3,as+1,4a+a,4x,1j+e,1l+2,1e+3,3+1,1y+2,11+4,2+7,1r,d+1,1h+8,b+3,3,2o+2,3,2+1,7,4h,4+7,m+1,1m+1,4,12+6,4+4,5g+7,3+2,2,o,2d+5,2,5+1,2+1,6n+3,7+1,2+1,s+1,2e+7,3,2+1,2z,2,3+5,2,2u+2,3+3,2+4,78+8,2+1,75+1,2,5,41+3,3+1,5,x+9,15+5,3+3,9,a+5,3+2,1b+c,2+1,bb+6,2+5,2,2b+l,3+6,2+1,2+1,3f+5,4,2+1,2+6,2,21+1,4,2,9o+1,470+8,at4+4,1o+6,t5,1s+3,2a,f5l+1,2+3,43o+2,a+7,1+7,3+6,v+3,45+2,1j0+1i,5+1d,9,f,n+4,2+e,11t+6,2+g,3+6,2+1,2+4,7a+6,c6+3,15t+6,32+6,1,gzau,v+2n,3l+6n"},i=1,s=2,a=4,o=8,l=16,c=32;let u;function f(E){if(!u){const x={R:s,L:i,D:a,C:l,U:c,T:o};u=new Map;for(let w in r){let R=0;r[w].split(",").forEach(L=>{let[A,U]=L.split("+");A=parseInt(A,36),U=U?parseInt(U,36):0,u.set(R+=A,x[w]);for(let P=U;P--;)u.set(++R,x[w])})}}return u.get(E)||c}const h=1,d=2,m=3,g=4,p=[null,"isol","init","fina","medi"];function _(E){const x=new Uint8Array(E.length);let w=c,R=h,L=-1;for(let A=0;A<E.length;A++){const U=E.codePointAt(A);let P=f(U)|0,I=h;P&o||(w&(i|a|l)?P&(s|a|l)?(I=m,(R===h||R===m)&&x[L]++):P&(i|c)&&(R===d||R===g)&&x[L]--:w&(s|c)&&(R===d||R===g)&&x[L]--,R=x[A]=I,w=P,L=A,U>65535&&A++)}return x}function M(E,x){const w=[];for(let L=0;L<x.length;L++){const A=x.codePointAt(L);A>65535&&L++,w.push(n.U.codeToGlyph(E,A))}const R=E.GSUB;if(R){const{lookupList:L,featureList:A}=R;let U;const P=/^(rlig|liga|mset|isol|init|fina|medi|half|pres|blws|ccmp)$/,I=[];A.forEach(F=>{if(P.test(F.tag))for(let O=0;O<F.tab.length;O++){if(I[F.tab[O]])continue;I[F.tab[O]]=!0;const q=L[F.tab[O]],z=/^(isol|init|fina|medi)$/.test(F.tag);z&&!U&&(U=_(x));for(let k=0;k<w.length;k++)(!U||!z||p[U[k]]===F.tag)&&n.U._applySubs(w,k,q,L)}})}return w}function y(E,x){const w=new Int16Array(x.length*3);let R=0;for(;R<x.length;R++){const P=x[R];if(P===-1)continue;w[R*3+2]=E.hmtx.aWidth[P];const I=E.GPOS;if(I){const F=I.lookupList;for(let O=0;O<F.length;O++){const q=F[O];for(let z=0;z<q.tabs.length;z++){const k=q.tabs[z];if(q.ltype===1){if(n._lctf.coverageIndex(k.coverage,P)!==-1&&k.pos){U(k.pos,R);break}}else if(q.ltype===2){let N=null,G=L();if(G!==-1){const K=n._lctf.coverageIndex(k.coverage,x[G]);if(K!==-1){if(k.fmt===1){const J=k.pairsets[K];for(let j=0;j<J.length;j++)J[j].gid2===P&&(N=J[j])}else if(k.fmt===2){const J=n.U._getGlyphClass(x[G],k.classDef1),j=n.U._getGlyphClass(P,k.classDef2);N=k.matrix[J][j]}if(N){N.val1&&U(N.val1,G),N.val2&&U(N.val2,R);break}}}}else if(q.ltype===4){const N=n._lctf.coverageIndex(k.markCoverage,P);if(N!==-1){const G=L(A),K=G===-1?-1:n._lctf.coverageIndex(k.baseCoverage,x[G]);if(K!==-1){const J=k.markArray[N],j=k.baseArray[K][J.markClass];w[R*3]=j.x-J.x+w[G*3]-w[G*3+2],w[R*3+1]=j.y-J.y+w[G*3+1];break}}}else if(q.ltype===6){const N=n._lctf.coverageIndex(k.mark1Coverage,P);if(N!==-1){const G=L();if(G!==-1){const K=x[G];if(v(E,K)===3){const J=n._lctf.coverageIndex(k.mark2Coverage,K);if(J!==-1){const j=k.mark1Array[N],V=k.mark2Array[J][j.markClass];w[R*3]=V.x-j.x+w[G*3]-w[G*3+2],w[R*3+1]=V.y-j.y+w[G*3+1];break}}}}}}}}else if(E.kern&&!E.cff){const F=L();if(F!==-1){const O=E.kern.glyph1.indexOf(x[F]);if(O!==-1){const q=E.kern.rval[O].glyph2.indexOf(P);q!==-1&&(w[F*3+2]+=E.kern.rval[O].vals[q])}}}}return w;function L(P){for(let I=R-1;I>=0;I--)if(x[I]!==-1&&(!P||P(x[I])))return I;return-1}function A(P){return v(E,P)===1}function U(P,I){for(let F=0;F<3;F++)w[I*3+F]+=P[F]||0}}function v(E,x){const w=E.GDEF&&E.GDEF.glyphClassDef;return w?n.U._getGlyphClass(x,w):0}function S(...E){for(let x=0;x<E.length;x++)if(typeof E[x]=="number")return E[x]}function b(E){const x=Object.create(null),w=E["OS/2"],R=E.hhea,L=E.head.unitsPerEm,A=S(w&&w.sTypoAscender,R&&R.ascender,L),U={unitsPerEm:L,ascender:A,descender:S(w&&w.sTypoDescender,R&&R.descender,0),capHeight:S(w&&w.sCapHeight,A),xHeight:S(w&&w.sxHeight,A),lineGap:S(w&&w.sTypoLineGap,R&&R.lineGap),supportsCodePoint(P){return n.U.codeToGlyph(E,P)>0},forEachGlyph(P,I,F,O){let q=0;const z=1/U.unitsPerEm*I,k=M(E,P);let N=0;const G=y(E,k);return k.forEach((K,J)=>{if(K!==-1){let j=x[K];if(!j){const{cmds:V,crds:Y}=n.U.glyphToPath(E,K);let Z="",fe=0;for(let Ne=0,Ae=V.length;Ne<Ae;Ne++){const be=t[V[Ne]];Z+=V[Ne];for(let ze=1;ze<=be;ze++)Z+=(ze>1?",":"")+Y[fe++]}let _e,le,de,Fe;if(Y.length){_e=le=1/0,de=Fe=-1/0;for(let Ne=0,Ae=Y.length;Ne<Ae;Ne+=2){let be=Y[Ne],ze=Y[Ne+1];be<_e&&(_e=be),ze<le&&(le=ze),be>de&&(de=be),ze>Fe&&(Fe=ze)}}else _e=de=le=Fe=0;j=x[K]={index:K,advanceWidth:E.hmtx.aWidth[K],xMin:_e,yMin:le,xMax:de,yMax:Fe,path:Z}}O.call(null,j,q+G[J*3]*z,G[J*3+1]*z,N),q+=G[J*3+2]*z,F&&(q+=F*I)}N+=P.codePointAt(N)>65535?2:1}),q}};return U}return function(x){const w=new Uint8Array(x,0,4),R=n._bin.readASCII(w,0,4);if(R==="wOFF")x=e(x);else if(R==="wOF2")throw new Error("woff2 fonts not supported");return b(n.parse(x)[0])}}const bb=Zs({name:"Typr Font Parser",dependencies:[xb,Mb,Sb],init(n,e,t){const r=n(),i=e();return t(r,i)}});/*!
Custom bundle of @unicode-font-resolver/client v1.0.2 (https://github.com/lojjic/unicode-font-resolver)
for use in Troika text rendering. 
Original MIT license applies
*/function yb(){return(function(n){var e=function(){this.buckets=new Map};e.prototype.add=function(y){var v=y>>5;this.buckets.set(v,(this.buckets.get(v)||0)|1<<(31&y))},e.prototype.has=function(y){var v=this.buckets.get(y>>5);return v!==void 0&&(v&1<<(31&y))!=0},e.prototype.serialize=function(){var y=[];return this.buckets.forEach((function(v,S){y.push((+S).toString(36)+":"+v.toString(36))})),y.join(",")},e.prototype.deserialize=function(y){var v=this;this.buckets.clear(),y.split(",").forEach((function(S){var b=S.split(":");v.buckets.set(parseInt(b[0],36),parseInt(b[1],36))}))};var t=Math.pow(2,8),r=t-1,i=~r;function s(y){var v=(function(b){return b&i})(y).toString(16),S=(function(b){return(b&i)+t-1})(y).toString(16);return"codepoint-index/plane"+(y>>16)+"/"+v+"-"+S+".json"}function a(y,v){var S=y&r,b=v.codePointAt(S/6|0);return((b=(b||48)-48)&1<<S%6)!=0}function o(y,v){var S;(S=y,S.replace(/U\+/gi,"").replace(/^,+|,+$/g,"").split(/,+/).map((function(b){return b.split("-").map((function(E){return parseInt(E.trim(),16)}))}))).forEach((function(b){var E=b[0],x=b[1];x===void 0&&(x=E),v(E,x)}))}function l(y,v){o(y,(function(S,b){for(var E=S;E<=b;E++)v(E)}))}var c={},u={},f=new WeakMap,h="https://cdn.jsdelivr.net/gh/lojjic/unicode-font-resolver@v1.0.1/packages/data";function d(y){var v=f.get(y);return v||(v=new e,l(y.ranges,(function(S){return v.add(S)})),f.set(y,v)),v}var m,g=new Map;function p(y,v,S){return y[v]?v:y[S]?S:(function(b){for(var E in b)return E})(y)}function _(y,v){var S=v;if(!y.includes(S)){S=1/0;for(var b=0;b<y.length;b++)Math.abs(y[b]-v)<Math.abs(S-v)&&(S=y[b])}return S}function M(y){return m||(m=new Set,l("9-D,20,85,A0,1680,2000-200A,2028-202F,205F,3000",(function(v){m.add(v)}))),m.has(y)}return n.CodePointSet=e,n.clearCache=function(){c={},u={}},n.getFontsForString=function(y,v){v===void 0&&(v={});var S,b=v.lang;b===void 0&&(b=new RegExp("\\p{Script=Hangul}","u").test(S=y)?"ko":new RegExp("\\p{Script=Hiragana}|\\p{Script=Katakana}","u").test(S)?"ja":"en");var E=v.category;E===void 0&&(E="sans-serif");var x=v.style;x===void 0&&(x="normal");var w=v.weight;w===void 0&&(w=400);var R=(v.dataUrl||h).replace(/\/$/g,""),L=new Map,A=new Uint8Array(y.length),U={},P={},I=new Array(y.length),F=new Map,O=!1;function q(N){var G=g.get(N);return G||(G=fetch(R+"/"+N).then((function(K){if(!K.ok)throw new Error(K.statusText);return K.json().then((function(J){if(!Array.isArray(J)||J[0]!==1)throw new Error("Incorrect schema version; need 1, got "+J[0]);return J[1]}))})).catch((function(K){if(R!==h)return O||(console.error('unicode-font-resolver: Failed loading from dataUrl "'+R+'", trying default CDN. '+K.message),O=!0),R=h,g.delete(N),q(N);throw K})),g.set(N,G)),G}for(var z=function(N){var G=y.codePointAt(N),K=s(G);I[N]=K,c[K]||F.has(K)||F.set(K,q(K).then((function(J){c[K]=J}))),G>65535&&(N++,k=N)},k=0;k<y.length;k++)z(k);return Promise.all(F.values()).then((function(){F.clear();for(var N=function(K){var J=y.codePointAt(K),j=null,V=c[I[K]],Y=void 0;for(var Z in V){var fe=P[Z];if(fe===void 0&&(fe=P[Z]=new RegExp(Z).test(b||"en")),fe){for(var _e in Y=Z,V[Z])if(a(J,V[Z][_e])){j=_e;break}break}}if(!j){e:for(var le in V)if(le!==Y){for(var de in V[le])if(a(J,V[le][de])){j=de;break e}}}j||(console.debug("No font coverage for U+"+J.toString(16)),j="latin"),I[K]=j,u[j]||F.has(j)||F.set(j,q("font-meta/"+j+".json").then((function(Fe){u[j]=Fe}))),J>65535&&(K++,G=K)},G=0;G<y.length;G++)N(G);return Promise.all(F.values())})).then((function(){for(var N,G=null,K=0;K<y.length;K++){var J=y.codePointAt(K);if(G&&(M(J)||d(G).has(J)))A[K]=A[K-1];else{G=u[I[K]];var j=U[G.id];if(!j){var V=G.typeforms,Y=p(V,E,"sans-serif"),Z=p(V[Y],x,"normal"),fe=_((N=V[Y])===null||N===void 0?void 0:N[Z],w);j=U[G.id]=R+"/font-files/"+G.id+"/"+Y+"."+Z+"."+fe+".woff"}var _e=L.get(j);_e==null&&(_e=L.size,L.set(j,_e)),A[K]=_e}J>65535&&(K++,A[K]=A[K-1])}return{fontUrls:Array.from(L.keys()),chars:A}}))},Object.defineProperty(n,"__esModule",{value:!0}),n})({})}function Tb(n,e){const t=Object.create(null),r=Object.create(null);function i(a,o){const l=c=>{console.error(`Failure loading font ${a}`,c)};try{const c=new XMLHttpRequest;c.open("get",a,!0),c.responseType="arraybuffer",c.onload=function(){if(c.status>=400)l(new Error(c.statusText));else if(c.status>0)try{const u=n(c.response);u.src=a,o(u)}catch(u){l(u)}},c.onerror=l,c.send()}catch(c){l(c)}}function s(a,o){let l=t[a];l?o(l):r[a]?r[a].push(o):(r[a]=[o],i(a,c=>{c.src=a,t[a]=c,r[a].forEach(u=>u(c)),delete r[a]}))}return function(a,o,{lang:l,fonts:c=[],style:u="normal",weight:f="normal",unicodeFontsURL:h}={}){const d=new Uint8Array(a.length),m=[];a.length||M();const g=new Map,p=[];if(u!=="italic"&&(u="normal"),typeof f!="number"&&(f=f==="bold"?700:400),c&&!Array.isArray(c)&&(c=[c]),c=c.slice().filter(v=>!v.lang||v.lang.test(l)).reverse(),c.length){let E=0;(function x(w=0){for(let R=w,L=a.length;R<L;R++){const A=a.codePointAt(R);if(E===1&&m[d[R-1]].supportsCodePoint(A)||R>0&&/\s/.test(a[R]))d[R]=d[R-1],E===2&&(p[p.length-1][1]=R);else for(let U=d[R],P=c.length;U<=P;U++)if(U===P){const I=E===2?p[p.length-1]:p[p.length]=[R,R];I[1]=R,E=2}else{d[R]=U;const{src:I,unicodeRange:F}=c[U];if(!F||y(A,F)){const O=t[I];if(!O){s(I,()=>{x(R)});return}if(O.supportsCodePoint(A)){let q=g.get(O);typeof q!="number"&&(q=m.length,m.push(O),g.set(O,q)),d[R]=q,E=1;break}}}A>65535&&R+1<L&&(d[R+1]=d[R],R++,E===2&&(p[p.length-1][1]=R))}_()})()}else p.push([0,a.length-1]),_();function _(){if(p.length){const v=p.map(S=>a.substring(S[0],S[1]+1)).join(`
`);e.getFontsForString(v,{lang:l||void 0,style:u,weight:f,dataUrl:h}).then(({fontUrls:S,chars:b})=>{const E=m.length;let x=0;p.forEach(R=>{for(let L=0,A=R[1]-R[0];L<=A;L++)d[R[0]+L]=b[x++]+E;x++});let w=0;S.forEach((R,L)=>{s(R,A=>{m[L+E]=A,++w===S.length&&M()})})})}else M()}function M(){o({chars:d,fonts:m})}function y(v,S){for(let b=0;b<S.length;b++){const[E,x=E]=S[b];if(E<=v&&v<=x)return!0}return!1}}}const Eb=Zs({name:"FontResolver",dependencies:[Tb,bb,yb],init(n,e,t){return n(e,t())}});function wb(n,e){const r=/[\u00AD\u034F\u061C\u115F-\u1160\u17B4-\u17B5\u180B-\u180E\u200B-\u200F\u202A-\u202E\u2060-\u206F\u3164\uFE00-\uFE0F\uFEFF\uFFA0\uFFF0-\uFFF8]/,i="[^\\S\\u00A0]",s=new RegExp(`${i}|[\\-\\u007C\\u00AD\\u2010\\u2012-\\u2014\\u2027\\u2056\\u2E17\\u2E40]`);function a({text:m,lang:g,fonts:p,style:_,weight:M,preResolvedFonts:y,unicodeFontsURL:v},S){const b=({chars:E,fonts:x})=>{let w,R;const L=[];for(let A=0;A<E.length;A++)E[A]!==R?(R=E[A],L.push(w={start:A,end:A,fontObj:x[E[A]]})):w.end=A;S(L)};y?b(y):n(m,b,{lang:g,fonts:p,style:_,weight:M,unicodeFontsURL:v})}function o({text:m="",font:g,lang:p,sdfGlyphSize:_=64,fontSize:M=400,fontWeight:y=1,fontStyle:v="normal",letterSpacing:S=0,lineHeight:b="normal",maxWidth:E=1/0,direction:x,textAlign:w="left",textIndent:R=0,whiteSpace:L="normal",overflowWrap:A="normal",anchorX:U=0,anchorY:P=0,metricsOnly:I=!1,unicodeFontsURL:F,preResolvedFonts:O=null,includeCaretPositions:q=!1,chunkedBoundsSize:z=8192,colorRanges:k=null},N){const G=f(),K={fontLoad:0,typesetting:0};m.indexOf("\r")>-1&&(console.info("Typesetter: got text with \\r chars; normalizing to \\n"),m=m.replace(/\r\n/g,`
`).replace(/\r/g,`
`)),M=+M,S=+S,E=+E,b=b||"normal",R=+R,a({text:m,lang:p,style:v,weight:y,fonts:typeof g=="string"?[{src:g}]:g,unicodeFontsURL:F,preResolvedFonts:O},J=>{K.fontLoad=f()-G;const j=isFinite(E);let V=null,Y=null,Z=null,fe=null,_e=null,le=null,de=null,Fe=null,Ne=0,Ae=0,be=L!=="nowrap";const ze=new Map,ge=f();let ke=R,B=0,ue=new h;const De=[ue];J.forEach(T=>{const{fontObj:H}=T,{ascender:Q,descender:oe,unitsPerEm:me,lineGap:Me,capHeight:ee,xHeight:re}=H;let he=ze.get(H);if(!he){const Ce=M/me,Ye=b==="normal"?(Q-oe+Me)*Ce:b*M,W=(Ye-(Q-oe)*Ce)/2,pe=Math.min(Ye,(Q-oe)*Ce),ie=(Q+oe)/2*Ce+pe/2;he={index:ze.size,src:H.src,fontObj:H,fontSizeMult:Ce,unitsPerEm:me,ascender:Q*Ce,descender:oe*Ce,capHeight:ee*Ce,xHeight:re*Ce,lineHeight:Ye,baseline:-W-Q*Ce,caretTop:ie,caretBottom:ie-pe},ze.set(H,he)}const{fontSizeMult:Re}=he,ve=m.slice(T.start,T.end+1);let Se,Ge;H.forEachGlyph(ve,M,S,(Ce,Ye,W,pe)=>{Ye+=B,pe+=T.start,Se=Ye,Ge=Ce;const ie=m.charAt(pe),we=Ce.advanceWidth*Re,xe=ue.count;let ae;if("isEmpty"in Ce||(Ce.isWhitespace=!!ie&&new RegExp(i).test(ie),Ce.canBreakAfter=!!ie&&s.test(ie),Ce.isEmpty=Ce.xMin===Ce.xMax||Ce.yMin===Ce.yMax||r.test(ie)),!Ce.isWhitespace&&!Ce.isEmpty&&Ae++,be&&j&&!Ce.isWhitespace&&Ye+we+ke>E&&xe){if(ue.glyphAt(xe-1).glyphObj.canBreakAfter)ae=new h,ke=-Ye;else for(let Ke=xe;Ke--;)if(Ke===0&&A==="break-word"){ae=new h,ke=-Ye;break}else if(ue.glyphAt(Ke).glyphObj.canBreakAfter){ae=ue.splitAt(Ke+1);const st=ae.glyphAt(0).x;ke-=st;for(let Qe=ae.count;Qe--;)ae.glyphAt(Qe).x-=st;break}ae&&(ue.isSoftWrapped=!0,ue=ae,De.push(ue),Ne=E)}let Pe=ue.glyphAt(ue.count);Pe.glyphObj=Ce,Pe.x=Ye+ke,Pe.y=W,Pe.width=we,Pe.charIndex=pe,Pe.fontData=he,ie===`
`&&(ue=new h,De.push(ue),ke=-(Ye+we+S*M)+R)}),B=Se+Ge.advanceWidth*Re+S*M});let ye=0;De.forEach(T=>{let H=!0;for(let Q=T.count;Q--;){const oe=T.glyphAt(Q);H&&!oe.glyphObj.isWhitespace&&(T.width=oe.x+oe.width,T.width>Ne&&(Ne=T.width),H=!1);let{lineHeight:me,capHeight:Me,xHeight:ee,baseline:re}=oe.fontData;me>T.lineHeight&&(T.lineHeight=me);const he=re-T.baseline;he<0&&(T.baseline+=he,T.cap+=he,T.ex+=he),T.cap=Math.max(T.cap,T.baseline+Me),T.ex=Math.max(T.ex,T.baseline+ee)}T.baseline-=ye,T.cap-=ye,T.ex-=ye,ye+=T.lineHeight});let ce=0,Te=0;if(U&&(typeof U=="number"?ce=-U:typeof U=="string"&&(ce=-Ne*(U==="left"?0:U==="center"?.5:U==="right"?1:c(U)))),P&&(typeof P=="number"?Te=-P:typeof P=="string"&&(Te=P==="top"?0:P==="top-baseline"?-De[0].baseline:P==="top-cap"?-De[0].cap:P==="top-ex"?-De[0].ex:P==="middle"?ye/2:P==="bottom"?ye:P==="bottom-baseline"?-De[De.length-1].baseline:c(P)*ye)),!I){const T=e.getEmbeddingLevels(m,x);V=new Uint16Array(Ae),Y=new Uint8Array(Ae),Z=new Float32Array(Ae*2),fe={},de=[1/0,1/0,-1/0,-1/0],Fe=[],q&&(le=new Float32Array(m.length*4)),k&&(_e=new Uint8Array(Ae*3));let H=0,Q=-1,oe=-1,me,Me;if(De.forEach((ee,re)=>{let{count:he,width:Re}=ee;if(he>0){let ve=0;for(let pe=he;pe--&&ee.glyphAt(pe).glyphObj.isWhitespace;)ve++;let Se=0,Ge=0;if(w==="center")Se=(Ne-Re)/2;else if(w==="right")Se=Ne-Re;else if(w==="justify"&&ee.isSoftWrapped){let pe=0;for(let ie=he-ve;ie--;)ee.glyphAt(ie).glyphObj.isWhitespace&&pe++;Ge=(Ne-Re)/pe}if(Ge||Se){let pe=0;for(let ie=0;ie<he;ie++){let we=ee.glyphAt(ie);const xe=we.glyphObj;we.x+=Se+pe,Ge!==0&&xe.isWhitespace&&ie<he-ve&&(pe+=Ge,we.width+=Ge)}}const Ce=e.getReorderSegments(m,T,ee.glyphAt(0).charIndex,ee.glyphAt(ee.count-1).charIndex);for(let pe=0;pe<Ce.length;pe++){const[ie,we]=Ce[pe];let xe=1/0,ae=-1/0;for(let Pe=0;Pe<he;Pe++)if(ee.glyphAt(Pe).charIndex>=ie){let Ke=Pe,st=Pe;for(;st<he;st++){let Qe=ee.glyphAt(st);if(Qe.charIndex>we)break;st<he-ve&&(xe=Math.min(xe,Qe.x),ae=Math.max(ae,Qe.x+Qe.width))}for(let Qe=Ke;Qe<st;Qe++){const Ht=ee.glyphAt(Qe);Ht.x=ae-(Ht.x+Ht.width-xe)}break}}let Ye;const W=pe=>Ye=pe;for(let pe=0;pe<he;pe++){const ie=ee.glyphAt(pe);Ye=ie.glyphObj;const we=Ye.index,xe=T.levels[ie.charIndex]&1;if(xe){const ae=e.getMirroredCharacter(m[ie.charIndex]);ae&&ie.fontData.fontObj.forEachGlyph(ae,0,0,W)}if(q){const{charIndex:ae,fontData:Pe}=ie,Ke=ie.x+ce,st=ie.x+ie.width+ce;le[ae*4]=xe?st:Ke,le[ae*4+1]=xe?Ke:st,le[ae*4+2]=ee.baseline+Pe.caretBottom+Te,le[ae*4+3]=ee.baseline+Pe.caretTop+Te;const Qe=ae-Q;Qe>1&&u(le,Q,Qe),Q=ae}if(k){const{charIndex:ae}=ie;for(;ae>oe;)oe++,k.hasOwnProperty(oe)&&(Me=k[oe])}if(!Ye.isWhitespace&&!Ye.isEmpty){const ae=H++,{fontSizeMult:Pe,src:Ke,index:st}=ie.fontData,Qe=fe[Ke]||(fe[Ke]={});Qe[we]||(Qe[we]={path:Ye.path,pathBounds:[Ye.xMin,Ye.yMin,Ye.xMax,Ye.yMax]});const Ht=ie.x+ce,jt=ie.y+ee.baseline+Te;Z[ae*2]=Ht,Z[ae*2+1]=jt;const Ln=Ht+Ye.xMin*Pe,di=jt+Ye.yMin*Pe,pi=Ht+Ye.xMax*Pe,qn=jt+Ye.yMax*Pe;Ln<de[0]&&(de[0]=Ln),di<de[1]&&(de[1]=di),pi>de[2]&&(de[2]=pi),qn>de[3]&&(de[3]=qn),ae%z===0&&(me={start:ae,end:ae,rect:[1/0,1/0,-1/0,-1/0]},Fe.push(me)),me.end++;const Lt=me.rect;if(Ln<Lt[0]&&(Lt[0]=Ln),di<Lt[1]&&(Lt[1]=di),pi>Lt[2]&&(Lt[2]=pi),qn>Lt[3]&&(Lt[3]=qn),V[ae]=we,Y[ae]=st,k){const ei=ae*3;_e[ei]=Me>>16&255,_e[ei+1]=Me>>8&255,_e[ei+2]=Me&255}}}}}),le){const ee=m.length-Q;ee>1&&u(le,Q,ee)}}const D=[];ze.forEach(({index:T,src:H,unitsPerEm:Q,ascender:oe,descender:me,lineHeight:Me,capHeight:ee,xHeight:re})=>{D[T]={src:H,unitsPerEm:Q,ascender:oe,descender:me,lineHeight:Me,capHeight:ee,xHeight:re}}),K.typesetting=f()-ge,N({glyphIds:V,glyphFontIndices:Y,glyphPositions:Z,glyphData:fe,fontData:D,caretPositions:le,glyphColors:_e,chunkedBounds:Fe,fontSize:M,topBaseline:Te+De[0].baseline,blockBounds:[ce,Te-ye,ce+Ne,Te],visibleBounds:de,timings:K})})}function l(m,g){o({...m,metricsOnly:!0},p=>{const[_,M,y,v]=p.blockBounds;g({width:y-_,height:v-M})})}function c(m){let g=m.match(/^([\d.]+)%$/),p=g?parseFloat(g[1]):NaN;return isNaN(p)?0:p/100}function u(m,g,p){const _=m[g*4],M=m[g*4+1],y=m[g*4+2],v=m[g*4+3],S=(M-_)/p;for(let b=0;b<p;b++){const E=(g+b)*4;m[E]=_+S*b,m[E+1]=_+S*(b+1),m[E+2]=y,m[E+3]=v}}function f(){return(self.performance||Date).now()}function h(){this.data=[]}const d=["glyphObj","x","y","width","charIndex","fontData"];return h.prototype={width:0,lineHeight:0,baseline:0,cap:0,ex:0,isSoftWrapped:!1,get count(){return Math.ceil(this.data.length/d.length)},glyphAt(m){let g=h.flyweight;return g.data=this.data,g.index=m,g},splitAt(m){let g=new h;return g.data=this.data.splice(m*d.length),g}},h.flyweight=d.reduce((m,g,p,_)=>(Object.defineProperty(m,g,{get(){return this.data[this.index*d.length+p]},set(M){this.data[this.index*d.length+p]=M}}),m),{data:null,index:0}),{typeset:o,measure:l}}const Gr=()=>(self.performance||Date).now(),Dl=Zm();let rp;function Ab(n,e,t,r,i,s,a,o,l,c,u=!0){return u?Cb(n,e,t,r,i,s,a,o,l,c).then(null,f=>(rp||(console.warn("WebGL SDF generation failed, falling back to JS",f),rp=!0),ap(n,e,t,r,i,s,a,o,l,c))):ap(n,e,t,r,i,s,a,o,l,c)}const Jo=[],Rb=5;let vh=0;function Jm(){const n=Gr();for(;Jo.length&&Gr()-n<Rb;)Jo.shift()();vh=Jo.length?setTimeout(Jm,0):0}const Cb=(...n)=>new Promise((e,t)=>{Jo.push(()=>{const r=Gr();try{Dl.webgl.generateIntoCanvas(...n),e({timing:Gr()-r})}catch(i){t(i)}}),vh||(vh=setTimeout(Jm,0))}),Pb=4,Db=2e3,sp={};let Ub=0;function ap(n,e,t,r,i,s,a,o,l,c){const u="TroikaTextSDFGenerator_JS_"+Ub++%Pb;let f=sp[u];return f||(f=sp[u]={workerModule:Zs({name:u,workerId:u,dependencies:[Zm,Gr],init(h,d){const m=h().javascript.generate;return function(...g){const p=d();return{textureData:m(...g),timing:d()-p}}},getTransferables(h){return[h.textureData.buffer]}}),requests:0,idleTimer:null}),f.requests++,clearTimeout(f.idleTimer),f.workerModule(n,e,t,r,i,s).then(({textureData:h,timing:d})=>{const m=Gr(),g=new Uint8Array(h.length*4);for(let p=0;p<h.length;p++)g[p*4+c]=h[p];return Dl.webglUtils.renderImageData(a,g,o,l,n,e,1<<3-c),d+=Gr()-m,--f.requests===0&&(f.idleTimer=setTimeout(()=>{cb(u)},Db)),{timing:d}})}function Lb(n){n._warm||(Dl.webgl.isSupported(n),n._warm=!0)}const Ib=Dl.webglUtils.resizeWebGLCanvasWithoutClearing,wa={unicodeFontsURL:null,sdfGlyphSize:64,sdfMargin:1/16,sdfExponent:9,textureWidth:2048},Fb=new lt;function Ts(){return(self.performance||Date).now()}const op=Object.create(null);function Nb(n,e){n=Bb({},n);const t=Ts(),r=[];if(n.font&&r.push({label:"user",src:kb(n.font)}),n.font=r,n.text=""+n.text,n.sdfGlyphSize=n.sdfGlyphSize||wa.sdfGlyphSize,n.unicodeFontsURL=n.unicodeFontsURL||wa.unicodeFontsURL,n.colorRanges!=null){let h={};for(let d in n.colorRanges)if(n.colorRanges.hasOwnProperty(d)){let m=n.colorRanges[d];typeof m!="number"&&(m=Fb.set(m).getHex()),h[d]=m}n.colorRanges=h}Object.freeze(n);const{textureWidth:i,sdfExponent:s}=wa,{sdfGlyphSize:a}=n,o=i/a*4;let l=op[a];if(!l){const h=document.createElement("canvas");h.width=i,h.height=a*256/o,l=op[a]={glyphCount:0,sdfGlyphSize:a,sdfCanvas:h,sdfTexture:new Zt(h,void 0,void 0,void 0,zt,zt),contextLost:!1,glyphsByFont:new Map},l.sdfTexture.generateMipmaps=!1,Ob(l)}const{sdfTexture:c,sdfCanvas:u}=l;t0(n).then(h=>{const{glyphIds:d,glyphFontIndices:m,fontData:g,glyphPositions:p,fontSize:_,timings:M}=h,y=[],v=new Float32Array(d.length*4);let S=0,b=0;const E=Ts(),x=g.map(U=>{let P=l.glyphsByFont.get(U.src);return P||l.glyphsByFont.set(U.src,P=new Map),P});d.forEach((U,P)=>{const I=m[P],{src:F,unitsPerEm:O}=g[I];let q=x[I].get(U);if(!q){const{path:K,pathBounds:J}=h.glyphData[F][U],j=Math.max(J[2]-J[0],J[3]-J[1])/a*(wa.sdfMargin*a+.5),V=l.glyphCount++,Y=[J[0]-j,J[1]-j,J[2]+j,J[3]+j];x[I].set(U,q={path:K,atlasIndex:V,sdfViewBox:Y}),y.push(q)}const{sdfViewBox:z}=q,k=p[b++],N=p[b++],G=_/O;v[S++]=k+z[0]*G,v[S++]=N+z[1]*G,v[S++]=k+z[2]*G,v[S++]=N+z[3]*G,d[P]=q.atlasIndex}),M.quads=(M.quads||0)+(Ts()-E);const w=Ts();M.sdf={};const R=u.height,L=Math.ceil(l.glyphCount/o),A=Math.pow(2,Math.ceil(Math.log2(L*a)));A>R&&(console.info(`Increasing SDF texture size ${R}->${A}`),Ib(u,i,A),c.dispose()),Promise.all(y.map(U=>Qm(U,l,n.gpuAccelerateSDF).then(({timing:P})=>{M.sdf[U.atlasIndex]=P}))).then(()=>{y.length&&!l.contextLost&&(e0(l),c.needsUpdate=!0),M.sdfTotal=Ts()-w,M.total=Ts()-t,e(Object.freeze({parameters:n,sdfTexture:c,sdfGlyphSize:a,sdfExponent:s,glyphBounds:v,glyphAtlasIndices:d,glyphColors:h.glyphColors,caretPositions:h.caretPositions,chunkedBounds:h.chunkedBounds,ascender:h.ascender,descender:h.descender,lineHeight:h.lineHeight,capHeight:h.capHeight,xHeight:h.xHeight,topBaseline:h.topBaseline,blockBounds:h.blockBounds,visibleBounds:h.visibleBounds,timings:h.timings}))})}),Promise.resolve().then(()=>{l.contextLost||Lb(u)})}function Qm({path:n,atlasIndex:e,sdfViewBox:t},{sdfGlyphSize:r,sdfCanvas:i,contextLost:s},a){if(s)return Promise.resolve({timing:-1});const{textureWidth:o,sdfExponent:l}=wa,c=Math.max(t[2]-t[0],t[3]-t[1]),u=Math.floor(e/4),f=u%(o/r)*r,h=Math.floor(u/(o/r))*r,d=e%4;return Ab(r,r,n,t,c,l,i,f,h,d,a)}function Ob(n){const e=n.sdfCanvas;e.addEventListener("webglcontextlost",t=>{console.log("Context Lost",t),t.preventDefault(),n.contextLost=!0}),e.addEventListener("webglcontextrestored",t=>{console.log("Context Restored",t),n.contextLost=!1;const r=[];n.glyphsByFont.forEach(i=>{i.forEach(s=>{r.push(Qm(s,n,!0))})}),Promise.all(r).then(()=>{e0(n),n.sdfTexture.needsUpdate=!0})})}function Bb(n,e){for(let t in e)e.hasOwnProperty(t)&&(n[t]=e[t]);return n}let Fo;function kb(n){return Fo||(Fo=typeof document>"u"?{}:document.createElement("a")),Fo.href=n,Fo.href}function e0(n){if(typeof createImageBitmap!="function"){console.info("Safari<15: applying SDF canvas workaround");const{sdfCanvas:e,sdfTexture:t}=n,{width:r,height:i}=e,s=n.sdfCanvas.getContext("webgl");let a=t.image.data;(!a||a.length!==r*i*4)&&(a=new Uint8Array(r*i*4),t.image={width:r,height:i,data:a},t.flipY=!1,t.isDataTexture=!0),s.readPixels(0,0,r,i,s.RGBA,s.UNSIGNED_BYTE,a)}}const zb=Zs({name:"Typesetter",dependencies:[wb,Eb,hb],init(n,e,t){return n(e,t())}}),t0=Zs({name:"Typesetter",dependencies:[zb],init(n){return function(e){return new Promise(t=>{n.typeset(e,t)})}},getTransferables(n){const e=[];for(let t in n)n[t]&&n[t].buffer&&e.push(n[t].buffer);return e}});t0.onMainThread;const lp={};function Gb(n){let e=lp[n];return e||(e=lp[n]=new $r(1,1,n,n).translate(.5,.5,0)),e}const Hb="aTroikaGlyphBounds",cp="aTroikaGlyphIndex",Vb="aTroikaGlyphColor";class Wb extends rv{constructor(){super(),this.detail=1,this.curveRadius=0,this.groups=[{start:0,count:1/0,materialIndex:0},{start:0,count:1/0,materialIndex:1}],this.boundingSphere=new js,this.boundingBox=new qs}computeBoundingSphere(){}computeBoundingBox(){}set detail(e){if(e!==this._detail){this._detail=e,(typeof e!="number"||e<1)&&(e=1);let t=Gb(e);["position","normal","uv"].forEach(r=>{this.attributes[r]=t.attributes[r].clone()}),this.setIndex(t.getIndex().clone())}}get detail(){return this._detail}set curveRadius(e){e!==this._curveRadius&&(this._curveRadius=e,this._updateBounds())}get curveRadius(){return this._curveRadius}updateGlyphs(e,t,r,i,s){this.updateAttributeData(Hb,e,4),this.updateAttributeData(cp,t,1),this.updateAttributeData(Vb,s,3),this._blockBounds=r,this._chunkedBounds=i,this.instanceCount=t.length,this._updateBounds()}_updateBounds(){const e=this._blockBounds;if(e){const{curveRadius:t,boundingBox:r}=this;if(t){const{PI:i,floor:s,min:a,max:o,sin:l,cos:c}=Math,u=i/2,f=i*2,h=Math.abs(t),d=e[0]/h,m=e[2]/h,g=s((d+u)/f)!==s((m+u)/f)?-h:a(l(d)*h,l(m)*h),p=s((d-u)/f)!==s((m-u)/f)?h:o(l(d)*h,l(m)*h),_=s((d+i)/f)!==s((m+i)/f)?h*2:o(h-c(d)*h,h-c(m)*h);r.min.set(g,e[1],t<0?-_:0),r.max.set(p,e[3],t<0?0:_)}else r.min.set(e[0],e[1],0),r.max.set(e[2],e[3],0);r.getBoundingSphere(this.boundingSphere)}}applyClipRect(e){let t=this.getAttribute(cp).count,r=this._chunkedBounds;if(r)for(let i=r.length;i--;){t=r[i].end;let s=r[i].rect;if(s[1]<e.w&&s[3]>e.y&&s[0]<e.z&&s[2]>e.x)break}this.instanceCount=t}updateAttributeData(e,t,r){const i=this.getAttribute(e);t?i&&i.array.length===t.length?(i.array.set(t),i.needsUpdate=!0):(this.setAttribute(e,new Y_(t,r)),delete this._maxInstanceCount,this.dispose()):i&&this.deleteAttribute(e)}}const Xb=`
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
`,Yb=`
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
`,qb=`
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
`,jb=`
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
`;function Kb(n){const e=_h(n,{chained:!0,extensions:{derivatives:!0},uniforms:{uTroikaSDFTexture:{value:null},uTroikaSDFTextureSize:{value:new We},uTroikaSDFGlyphSize:{value:0},uTroikaSDFExponent:{value:0},uTroikaTotalBounds:{value:new Ct(0,0,0,0)},uTroikaClipRect:{value:new Ct(0,0,0,0)},uTroikaEdgeOffset:{value:0},uTroikaFillOpacity:{value:1},uTroikaPositionOffset:{value:new We},uTroikaCurveRadius:{value:0},uTroikaBlurRadius:{value:0},uTroikaStrokeWidth:{value:0},uTroikaStrokeColor:{value:new lt},uTroikaStrokeOpacity:{value:1},uTroikaOrient:{value:new nt},uTroikaUseGlyphColors:{value:!0},uTroikaSDFDebug:{value:!1}},vertexDefs:Xb,vertexTransform:Yb,fragmentDefs:qb,fragmentColorTransform:jb,customRewriter({vertexShader:t,fragmentShader:r}){let i=/\buniform\s+vec3\s+diffuse\b/;return i.test(r)&&(r=r.replace(i,"varying vec3 vTroikaGlyphColor").replace(/\bdiffuse\b/g,"vTroikaGlyphColor"),i.test(t)||(t=t.replace($m,`uniform vec3 diffuse;
$&
vTroikaGlyphColor = uTroikaUseGlyphColors ? aTroikaGlyphColor / 255.0 : diffuse;
`))),{vertexShader:t,fragmentShader:r}}});return e.transparent=!0,e.forceSinglePass=!0,Object.defineProperties(e,{isTroikaTextMaterial:{value:!0},shadowSide:{get(){return this.side},set(){}}}),e}const ef=new $h({color:16777215,side:wn,transparent:!0}),up=8421504,hp=new Ot,No=new X,Oc=new X,Ma=[],Zb=new X,Bc="+x+y";function fp(n){return Array.isArray(n)?n[0]:n}let n0=()=>{const n=new Wn(new $r(1,1),ef);return n0=()=>n,n},i0=()=>{const n=new Wn(new $r(1,1,32,1),ef);return i0=()=>n,n};const $b={type:"syncstart"},Jb={type:"synccomplete"},r0=["font","fontSize","fontStyle","fontWeight","lang","letterSpacing","lineHeight","maxWidth","overflowWrap","text","direction","textAlign","textIndent","whiteSpace","anchorX","anchorY","colorRanges","sdfGlyphSize"],Qb=r0.concat("material","color","depthOffset","clipRect","curveRadius","orientation","glyphGeometryDetail");class xh extends Wn{constructor(){const e=new Wb;super(e,null),this.text="",this.anchorX=0,this.anchorY=0,this.curveRadius=0,this.direction="auto",this.font=null,this.unicodeFontsURL=null,this.fontSize=.1,this.fontWeight="normal",this.fontStyle="normal",this.lang=null,this.letterSpacing=0,this.lineHeight="normal",this.maxWidth=1/0,this.overflowWrap="normal",this.textAlign="left",this.textIndent=0,this.whiteSpace="normal",this.material=null,this.color=null,this.colorRanges=null,this.outlineWidth=0,this.outlineColor=0,this.outlineOpacity=1,this.outlineBlur=0,this.outlineOffsetX=0,this.outlineOffsetY=0,this.strokeWidth=0,this.strokeColor=up,this.strokeOpacity=1,this.fillOpacity=1,this.depthOffset=0,this.clipRect=null,this.orientation=Bc,this.glyphGeometryDetail=1,this.sdfGlyphSize=null,this.gpuAccelerateSDF=!0,this.debugSDF=!1}sync(e){this._needsSync&&(this._needsSync=!1,this._isSyncing?(this._queuedSyncs||(this._queuedSyncs=[])).push(e):(this._isSyncing=!0,this.dispatchEvent($b),Nb({text:this.text,font:this.font,lang:this.lang,fontSize:this.fontSize||.1,fontWeight:this.fontWeight||"normal",fontStyle:this.fontStyle||"normal",letterSpacing:this.letterSpacing||0,lineHeight:this.lineHeight||"normal",maxWidth:this.maxWidth,direction:this.direction||"auto",textAlign:this.textAlign,textIndent:this.textIndent,whiteSpace:this.whiteSpace,overflowWrap:this.overflowWrap,anchorX:this.anchorX,anchorY:this.anchorY,colorRanges:this.colorRanges,includeCaretPositions:!0,sdfGlyphSize:this.sdfGlyphSize,gpuAccelerateSDF:this.gpuAccelerateSDF,unicodeFontsURL:this.unicodeFontsURL},t=>{this._isSyncing=!1,this._textRenderInfo=t,this.geometry.updateGlyphs(t.glyphBounds,t.glyphAtlasIndices,t.blockBounds,t.chunkedBounds,t.glyphColors);const r=this._queuedSyncs;r&&(this._queuedSyncs=null,this._needsSync=!0,this.sync(()=>{r.forEach(i=>i&&i())})),this.dispatchEvent(Jb),e&&e()})))}onBeforeRender(e,t,r,i,s,a){this.sync(),s.isTroikaTextMaterial&&this._prepareForRender(s)}dispose(){this.geometry.dispose()}get textRenderInfo(){return this._textRenderInfo||null}createDerivedMaterial(e){return Kb(e)}get material(){let e=this._derivedMaterial;const t=this._baseMaterial||this._defaultMaterial||(this._defaultMaterial=ef.clone());if((!e||!e.isDerivedFrom(t))&&(e=this._derivedMaterial=this.createDerivedMaterial(t),t.addEventListener("dispose",function r(){t.removeEventListener("dispose",r),e.dispose()})),this.hasOutline()){let r=e._outlineMtl;return r||(r=e._outlineMtl=Object.create(e,{id:{value:e.id+.1}}),r.isTextOutlineMaterial=!0,r.depthWrite=!1,r.map=null,e.addEventListener("dispose",function i(){e.removeEventListener("dispose",i),r.dispose()})),[r,e]}else return e}set material(e){e&&e.isTroikaTextMaterial?(this._derivedMaterial=e,this._baseMaterial=e.baseMaterial):this._baseMaterial=e}hasOutline(){return!!(this.outlineWidth||this.outlineBlur||this.outlineOffsetX||this.outlineOffsetY)}get glyphGeometryDetail(){return this.geometry.detail}set glyphGeometryDetail(e){this.geometry.detail=e}get curveRadius(){return this.geometry.curveRadius}set curveRadius(e){this.geometry.curveRadius=e}get customDepthMaterial(){return fp(this.material).getDepthMaterial()}set customDepthMaterial(e){}get customDistanceMaterial(){return fp(this.material).getDistanceMaterial()}set customDistanceMaterial(e){}_prepareForRender(e){const t=e.isTextOutlineMaterial,r=e.uniforms,i=this.textRenderInfo;if(i){const{sdfTexture:o,blockBounds:l}=i;r.uTroikaSDFTexture.value=o,r.uTroikaSDFTextureSize.value.set(o.image.width,o.image.height),r.uTroikaSDFGlyphSize.value=i.sdfGlyphSize,r.uTroikaSDFExponent.value=i.sdfExponent,r.uTroikaTotalBounds.value.fromArray(l),r.uTroikaUseGlyphColors.value=!t&&!!i.glyphColors;let c=0,u=0,f=0,h,d,m,g=0,p=0;if(t){let{outlineWidth:M,outlineOffsetX:y,outlineOffsetY:v,outlineBlur:S,outlineOpacity:b}=this;c=this._parsePercent(M)||0,u=Math.max(0,this._parsePercent(S)||0),h=b,g=this._parsePercent(y)||0,p=this._parsePercent(v)||0}else f=Math.max(0,this._parsePercent(this.strokeWidth)||0),f&&(m=this.strokeColor,r.uTroikaStrokeColor.value.set(m??up),d=this.strokeOpacity,d==null&&(d=1)),h=this.fillOpacity;r.uTroikaEdgeOffset.value=c,r.uTroikaPositionOffset.value.set(g,p),r.uTroikaBlurRadius.value=u,r.uTroikaStrokeWidth.value=f,r.uTroikaStrokeOpacity.value=d,r.uTroikaFillOpacity.value=h??1,r.uTroikaCurveRadius.value=this.curveRadius||0;let _=this.clipRect;if(_&&Array.isArray(_)&&_.length===4)r.uTroikaClipRect.value.fromArray(_);else{const M=(this.fontSize||.1)*100;r.uTroikaClipRect.value.set(l[0]-M,l[1]-M,l[2]+M,l[3]+M)}this.geometry.applyClipRect(r.uTroikaClipRect.value)}r.uTroikaSDFDebug.value=!!this.debugSDF,e.polygonOffset=!!this.depthOffset,e.polygonOffsetFactor=e.polygonOffsetUnits=this.depthOffset||0;const s=t?this.outlineColor||0:this.color;if(s==null)delete e.color;else{const o=e.hasOwnProperty("color")?e.color:e.color=new lt;(s!==o._input||typeof s=="object")&&o.set(o._input=s)}let a=this.orientation||Bc;if(a!==e._orientation){let o=r.uTroikaOrient.value;a=a.replace(/[^-+xyz]/g,"");let l=a!==Bc&&a.match(/^([-+])([xyz])([-+])([xyz])$/);if(l){let[,c,u,f,h]=l;No.set(0,0,0)[u]=c==="-"?1:-1,Oc.set(0,0,0)[h]=f==="-"?-1:1,hp.lookAt(Zb,No.cross(Oc),Oc),o.setFromMatrix4(hp)}else o.identity();e._orientation=a}}_parsePercent(e){if(typeof e=="string"){let t=e.match(/^(-?[\d.]+)%$/),r=t?parseFloat(t[1]):NaN;e=(isNaN(r)?0:r/100)*this.fontSize}return e}localPositionToTextCoords(e,t=new We){t.copy(e);const r=this.curveRadius;return r&&(t.x=Math.atan2(e.x,Math.abs(r)-Math.abs(e.z))*Math.abs(r)),t}worldPositionToTextCoords(e,t=new We){return No.copy(e),this.localPositionToTextCoords(this.worldToLocal(No),t)}raycast(e,t){const{textRenderInfo:r,curveRadius:i}=this;if(r){const s=r.blockBounds,a=i?i0():n0(),o=a.geometry,{position:l,uv:c}=o.attributes;for(let u=0;u<c.count;u++){let f=s[0]+c.getX(u)*(s[2]-s[0]);const h=s[1]+c.getY(u)*(s[3]-s[1]);let d=0;i&&(d=i-Math.cos(f/i)*i,f=Math.sin(f/i)*i),l.setXYZ(u,f,h,d)}o.boundingSphere=this.geometry.boundingSphere,o.boundingBox=this.geometry.boundingBox,a.matrixWorld=this.matrixWorld,a.material.side=this.material.side,Ma.length=0,a.raycast(e,Ma);for(let u=0;u<Ma.length;u++)Ma[u].object=this,t.push(Ma[u])}}copy(e){const t=this.geometry;return super.copy(e),this.geometry=t,Qb.forEach(r=>{this[r]=e[r]}),this}clone(){return new this.constructor().copy(this)}}r0.forEach(n=>{const e="_private_"+n;Object.defineProperty(xh.prototype,n,{get(){return this[e]},set(t){t!==this[e]&&(this[e]=t,this._needsSync=!0)}})});new lt;const dp={type:"change"},tf={type:"start"},s0={type:"end"},Oo=new Rl,pp=new lr,ey=Math.cos(70*E_.DEG2RAD),Kt=new X,Tn=2*Math.PI,St={NONE:-1,ROTATE:0,DOLLY:1,PAN:2,TOUCH_ROTATE:3,TOUCH_PAN:4,TOUCH_DOLLY_PAN:5,TOUCH_DOLLY_ROTATE:6},kc=1e-6;class ty extends lv{constructor(e,t=null){super(e,t),this.state=St.NONE,this.target=new X,this.cursor=new X,this.minDistance=0,this.maxDistance=1/0,this.minZoom=0,this.maxZoom=1/0,this.minTargetRadius=0,this.maxTargetRadius=1/0,this.minPolarAngle=0,this.maxPolarAngle=Math.PI,this.minAzimuthAngle=-1/0,this.maxAzimuthAngle=1/0,this.enableDamping=!1,this.dampingFactor=.05,this.enableZoom=!0,this.zoomSpeed=1,this.enableRotate=!0,this.rotateSpeed=1,this.keyRotateSpeed=1,this.enablePan=!0,this.panSpeed=1,this.screenSpacePanning=!0,this.keyPanSpeed=7,this.zoomToCursor=!1,this.autoRotate=!1,this.autoRotateSpeed=2,this.keys={LEFT:"ArrowLeft",UP:"ArrowUp",RIGHT:"ArrowRight",BOTTOM:"ArrowDown"},this.mouseButtons={LEFT:Ps.ROTATE,MIDDLE:Ps.DOLLY,RIGHT:Ps.PAN},this.touches={ONE:As.ROTATE,TWO:As.DOLLY_PAN},this.target0=this.target.clone(),this.position0=this.object.position.clone(),this.zoom0=this.object.zoom,this._cursorStyle="auto",this._domElementKeyEvents=null,this._lastPosition=new X,this._lastQuaternion=new vr,this._lastTargetPosition=new X,this._quat=new vr().setFromUnitVectors(e.up,new X(0,1,0)),this._quatInverse=this._quat.clone().invert(),this._spherical=new Ad,this._sphericalDelta=new Ad,this._scale=1,this._panOffset=new X,this._rotateStart=new We,this._rotateEnd=new We,this._rotateDelta=new We,this._panStart=new We,this._panEnd=new We,this._panDelta=new We,this._dollyStart=new We,this._dollyEnd=new We,this._dollyDelta=new We,this._dollyDirection=new X,this._mouse=new We,this._performCursorZoom=!1,this._pointers=[],this._pointerPositions={},this._controlActive=!1,this._onPointerMove=iy.bind(this),this._onPointerDown=ny.bind(this),this._onPointerUp=ry.bind(this),this._onContextMenu=hy.bind(this),this._onMouseWheel=oy.bind(this),this._onKeyDown=ly.bind(this),this._onTouchStart=cy.bind(this),this._onTouchMove=uy.bind(this),this._onMouseDown=sy.bind(this),this._onMouseMove=ay.bind(this),this._interceptControlDown=fy.bind(this),this._interceptControlUp=dy.bind(this),this.domElement!==null&&this.connect(this.domElement),this.update()}set cursorStyle(e){this._cursorStyle=e,e==="grab"?this.domElement.style.cursor="grab":this.domElement.style.cursor="auto"}get cursorStyle(){return this._cursorStyle}connect(e){super.connect(e),this.domElement.addEventListener("pointerdown",this._onPointerDown),this.domElement.addEventListener("pointercancel",this._onPointerUp),this.domElement.addEventListener("contextmenu",this._onContextMenu),this.domElement.addEventListener("wheel",this._onMouseWheel,{passive:!1}),this.domElement.getRootNode().addEventListener("keydown",this._interceptControlDown,{passive:!0,capture:!0}),this.domElement.style.touchAction="none"}disconnect(){this.domElement.removeEventListener("pointerdown",this._onPointerDown),this.domElement.ownerDocument.removeEventListener("pointermove",this._onPointerMove),this.domElement.ownerDocument.removeEventListener("pointerup",this._onPointerUp),this.domElement.removeEventListener("pointercancel",this._onPointerUp),this.domElement.removeEventListener("wheel",this._onMouseWheel),this.domElement.removeEventListener("contextmenu",this._onContextMenu),this.stopListenToKeyEvents(),this.domElement.getRootNode().removeEventListener("keydown",this._interceptControlDown,{capture:!0}),this.domElement.style.touchAction=""}dispose(){this.disconnect()}getPolarAngle(){return this._spherical.phi}getAzimuthalAngle(){return this._spherical.theta}getDistance(){return this.object.position.distanceTo(this.target)}listenToKeyEvents(e){e.addEventListener("keydown",this._onKeyDown),this._domElementKeyEvents=e}stopListenToKeyEvents(){this._domElementKeyEvents!==null&&(this._domElementKeyEvents.removeEventListener("keydown",this._onKeyDown),this._domElementKeyEvents=null)}saveState(){this.target0.copy(this.target),this.position0.copy(this.object.position),this.zoom0=this.object.zoom}reset(){this.target.copy(this.target0),this.object.position.copy(this.position0),this.object.zoom=this.zoom0,this.object.updateProjectionMatrix(),this.dispatchEvent(dp),this.update(),this.state=St.NONE}pan(e,t){this._pan(e,t),this.update()}dollyIn(e){this._dollyIn(e),this.update()}dollyOut(e){this._dollyOut(e),this.update()}rotateLeft(e){this._rotateLeft(e),this.update()}rotateUp(e){this._rotateUp(e),this.update()}update(e=null){const t=this.object.position;Kt.copy(t).sub(this.target),Kt.applyQuaternion(this._quat),this._spherical.setFromVector3(Kt),this.autoRotate&&this.state===St.NONE&&this._rotateLeft(this._getAutoRotationAngle(e)),this.enableDamping?(this._spherical.theta+=this._sphericalDelta.theta*this.dampingFactor,this._spherical.phi+=this._sphericalDelta.phi*this.dampingFactor):(this._spherical.theta+=this._sphericalDelta.theta,this._spherical.phi+=this._sphericalDelta.phi);let r=this.minAzimuthAngle,i=this.maxAzimuthAngle;isFinite(r)&&isFinite(i)&&(r<-Math.PI?r+=Tn:r>Math.PI&&(r-=Tn),i<-Math.PI?i+=Tn:i>Math.PI&&(i-=Tn),r<=i?this._spherical.theta=Math.max(r,Math.min(i,this._spherical.theta)):this._spherical.theta=this._spherical.theta>(r+i)/2?Math.max(r,this._spherical.theta):Math.min(i,this._spherical.theta)),this._spherical.phi=Math.max(this.minPolarAngle,Math.min(this.maxPolarAngle,this._spherical.phi)),this._spherical.makeSafe(),this.enableDamping===!0?this.target.addScaledVector(this._panOffset,this.dampingFactor):this.target.add(this._panOffset),this.target.sub(this.cursor),this.target.clampLength(this.minTargetRadius,this.maxTargetRadius),this.target.add(this.cursor);let s=!1;if(this.zoomToCursor&&this._performCursorZoom||this.object.isOrthographicCamera)this._spherical.radius=this._clampDistance(this._spherical.radius);else{const a=this._spherical.radius;this._spherical.radius=this._clampDistance(this._spherical.radius*this._scale),s=a!=this._spherical.radius}if(Kt.setFromSpherical(this._spherical),Kt.applyQuaternion(this._quatInverse),t.copy(this.target).add(Kt),this.object.lookAt(this.target),this.enableDamping===!0?(this._sphericalDelta.theta*=1-this.dampingFactor,this._sphericalDelta.phi*=1-this.dampingFactor,this._panOffset.multiplyScalar(1-this.dampingFactor)):(this._sphericalDelta.set(0,0,0),this._panOffset.set(0,0,0)),this.zoomToCursor&&this._performCursorZoom){let a=null;if(this.object.isPerspectiveCamera){const o=Kt.length();a=this._clampDistance(o*this._scale);const l=o-a;this.object.position.addScaledVector(this._dollyDirection,l),this.object.updateMatrixWorld(),s=!!l}else if(this.object.isOrthographicCamera){const o=new X(this._mouse.x,this._mouse.y,0);o.unproject(this.object);const l=this.object.zoom;this.object.zoom=Math.max(this.minZoom,Math.min(this.maxZoom,this.object.zoom/this._scale)),this.object.updateProjectionMatrix(),s=l!==this.object.zoom;const c=new X(this._mouse.x,this._mouse.y,0);c.unproject(this.object),this.object.position.sub(c).add(o),this.object.updateMatrixWorld(),a=Kt.length()}else console.warn("WARNING: OrbitControls.js encountered an unknown camera type - zoom to cursor disabled."),this.zoomToCursor=!1;a!==null&&(this.screenSpacePanning?this.target.set(0,0,-1).transformDirection(this.object.matrix).multiplyScalar(a).add(this.object.position):(Oo.origin.copy(this.object.position),Oo.direction.set(0,0,-1).transformDirection(this.object.matrix),Math.abs(this.object.up.dot(Oo.direction))<ey?this.object.lookAt(this.target):(pp.setFromNormalAndCoplanarPoint(this.object.up,this.target),Oo.intersectPlane(pp,this.target))))}else if(this.object.isOrthographicCamera){const a=this.object.zoom;this.object.zoom=Math.max(this.minZoom,Math.min(this.maxZoom,this.object.zoom/this._scale)),a!==this.object.zoom&&(this.object.updateProjectionMatrix(),s=!0)}return this._scale=1,this._performCursorZoom=!1,s||this._lastPosition.distanceToSquared(this.object.position)>kc||8*(1-this._lastQuaternion.dot(this.object.quaternion))>kc||this._lastTargetPosition.distanceToSquared(this.target)>kc?(this.dispatchEvent(dp),this._lastPosition.copy(this.object.position),this._lastQuaternion.copy(this.object.quaternion),this._lastTargetPosition.copy(this.target),!0):!1}_getAutoRotationAngle(e){return e!==null?Tn/60*this.autoRotateSpeed*e:Tn/60/60*this.autoRotateSpeed}_getZoomScale(e){const t=Math.abs(e*.01);return Math.pow(.95,this.zoomSpeed*t)}_rotateLeft(e){this._sphericalDelta.theta-=e}_rotateUp(e){this._sphericalDelta.phi-=e}_panLeft(e,t){Kt.setFromMatrixColumn(t,0),Kt.multiplyScalar(-e),this._panOffset.add(Kt)}_panUp(e,t){this.screenSpacePanning===!0?Kt.setFromMatrixColumn(t,1):(Kt.setFromMatrixColumn(t,0),Kt.crossVectors(this.object.up,Kt)),Kt.multiplyScalar(e),this._panOffset.add(Kt)}_pan(e,t){const r=this.domElement;if(this.object.isPerspectiveCamera){const i=this.object.position;Kt.copy(i).sub(this.target);let s=Kt.length();s*=Math.tan(this.object.fov/2*Math.PI/180),this._panLeft(2*e*s/r.clientHeight,this.object.matrix),this._panUp(2*t*s/r.clientHeight,this.object.matrix)}else this.object.isOrthographicCamera?(this._panLeft(e*(this.object.right-this.object.left)/this.object.zoom/r.clientWidth,this.object.matrix),this._panUp(t*(this.object.top-this.object.bottom)/this.object.zoom/r.clientHeight,this.object.matrix)):(console.warn("WARNING: OrbitControls.js encountered an unknown camera type - pan disabled."),this.enablePan=!1)}_dollyOut(e){this.object.isPerspectiveCamera||this.object.isOrthographicCamera?this._scale/=e:(console.warn("WARNING: OrbitControls.js encountered an unknown camera type - dolly/zoom disabled."),this.enableZoom=!1)}_dollyIn(e){this.object.isPerspectiveCamera||this.object.isOrthographicCamera?this._scale*=e:(console.warn("WARNING: OrbitControls.js encountered an unknown camera type - dolly/zoom disabled."),this.enableZoom=!1)}_updateZoomParameters(e,t){if(!this.zoomToCursor)return;this._performCursorZoom=!0;const r=this.domElement.getBoundingClientRect(),i=e-r.left,s=t-r.top,a=r.width,o=r.height;this._mouse.x=i/a*2-1,this._mouse.y=-(s/o)*2+1,this._dollyDirection.set(this._mouse.x,this._mouse.y,1).unproject(this.object).sub(this.object.position).normalize()}_clampDistance(e){return Math.max(this.minDistance,Math.min(this.maxDistance,e))}_handleMouseDownRotate(e){this._rotateStart.set(e.clientX,e.clientY)}_handleMouseDownDolly(e){this._updateZoomParameters(e.clientX,e.clientX),this._dollyStart.set(e.clientX,e.clientY)}_handleMouseDownPan(e){this._panStart.set(e.clientX,e.clientY)}_handleMouseMoveRotate(e){this._rotateEnd.set(e.clientX,e.clientY),this._rotateDelta.subVectors(this._rotateEnd,this._rotateStart).multiplyScalar(this.rotateSpeed);const t=this.domElement;this._rotateLeft(Tn*this._rotateDelta.x/t.clientHeight),this._rotateUp(Tn*this._rotateDelta.y/t.clientHeight),this._rotateStart.copy(this._rotateEnd),this.update()}_handleMouseMoveDolly(e){this._dollyEnd.set(e.clientX,e.clientY),this._dollyDelta.subVectors(this._dollyEnd,this._dollyStart),this._dollyDelta.y>0?this._dollyOut(this._getZoomScale(this._dollyDelta.y)):this._dollyDelta.y<0&&this._dollyIn(this._getZoomScale(this._dollyDelta.y)),this._dollyStart.copy(this._dollyEnd),this.update()}_handleMouseMovePan(e){this._panEnd.set(e.clientX,e.clientY),this._panDelta.subVectors(this._panEnd,this._panStart).multiplyScalar(this.panSpeed),this._pan(this._panDelta.x,this._panDelta.y),this._panStart.copy(this._panEnd),this.update()}_handleMouseWheel(e){this._updateZoomParameters(e.clientX,e.clientY),e.deltaY<0?this._dollyIn(this._getZoomScale(e.deltaY)):e.deltaY>0&&this._dollyOut(this._getZoomScale(e.deltaY)),this.update()}_handleKeyDown(e){let t=!1;switch(e.code){case this.keys.UP:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateUp(Tn*this.keyRotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(0,this.keyPanSpeed),t=!0;break;case this.keys.BOTTOM:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateUp(-Tn*this.keyRotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(0,-this.keyPanSpeed),t=!0;break;case this.keys.LEFT:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateLeft(Tn*this.keyRotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(this.keyPanSpeed,0),t=!0;break;case this.keys.RIGHT:e.ctrlKey||e.metaKey||e.shiftKey?this.enableRotate&&this._rotateLeft(-Tn*this.keyRotateSpeed/this.domElement.clientHeight):this.enablePan&&this._pan(-this.keyPanSpeed,0),t=!0;break}t&&(e.preventDefault(),this.update())}_handleTouchStartRotate(e){if(this._pointers.length===1)this._rotateStart.set(e.pageX,e.pageY);else{const t=this._getSecondPointerPosition(e),r=.5*(e.pageX+t.x),i=.5*(e.pageY+t.y);this._rotateStart.set(r,i)}}_handleTouchStartPan(e){if(this._pointers.length===1)this._panStart.set(e.pageX,e.pageY);else{const t=this._getSecondPointerPosition(e),r=.5*(e.pageX+t.x),i=.5*(e.pageY+t.y);this._panStart.set(r,i)}}_handleTouchStartDolly(e){const t=this._getSecondPointerPosition(e),r=e.pageX-t.x,i=e.pageY-t.y,s=Math.sqrt(r*r+i*i);this._dollyStart.set(0,s)}_handleTouchStartDollyPan(e){this.enableZoom&&this._handleTouchStartDolly(e),this.enablePan&&this._handleTouchStartPan(e)}_handleTouchStartDollyRotate(e){this.enableZoom&&this._handleTouchStartDolly(e),this.enableRotate&&this._handleTouchStartRotate(e)}_handleTouchMoveRotate(e){if(this._pointers.length==1)this._rotateEnd.set(e.pageX,e.pageY);else{const r=this._getSecondPointerPosition(e),i=.5*(e.pageX+r.x),s=.5*(e.pageY+r.y);this._rotateEnd.set(i,s)}this._rotateDelta.subVectors(this._rotateEnd,this._rotateStart).multiplyScalar(this.rotateSpeed);const t=this.domElement;this._rotateLeft(Tn*this._rotateDelta.x/t.clientHeight),this._rotateUp(Tn*this._rotateDelta.y/t.clientHeight),this._rotateStart.copy(this._rotateEnd)}_handleTouchMovePan(e){if(this._pointers.length===1)this._panEnd.set(e.pageX,e.pageY);else{const t=this._getSecondPointerPosition(e),r=.5*(e.pageX+t.x),i=.5*(e.pageY+t.y);this._panEnd.set(r,i)}this._panDelta.subVectors(this._panEnd,this._panStart).multiplyScalar(this.panSpeed),this._pan(this._panDelta.x,this._panDelta.y),this._panStart.copy(this._panEnd)}_handleTouchMoveDolly(e){const t=this._getSecondPointerPosition(e),r=e.pageX-t.x,i=e.pageY-t.y,s=Math.sqrt(r*r+i*i);this._dollyEnd.set(0,s),this._dollyDelta.set(0,Math.pow(this._dollyEnd.y/this._dollyStart.y,this.zoomSpeed)),this._dollyOut(this._dollyDelta.y),this._dollyStart.copy(this._dollyEnd);const a=(e.pageX+t.x)*.5,o=(e.pageY+t.y)*.5;this._updateZoomParameters(a,o)}_handleTouchMoveDollyPan(e){this.enableZoom&&this._handleTouchMoveDolly(e),this.enablePan&&this._handleTouchMovePan(e)}_handleTouchMoveDollyRotate(e){this.enableZoom&&this._handleTouchMoveDolly(e),this.enableRotate&&this._handleTouchMoveRotate(e)}_addPointer(e){this._pointers.push(e.pointerId)}_removePointer(e){delete this._pointerPositions[e.pointerId];for(let t=0;t<this._pointers.length;t++)if(this._pointers[t]==e.pointerId){this._pointers.splice(t,1);return}}_isTrackingPointer(e){for(let t=0;t<this._pointers.length;t++)if(this._pointers[t]==e.pointerId)return!0;return!1}_trackPointer(e){let t=this._pointerPositions[e.pointerId];t===void 0&&(t=new We,this._pointerPositions[e.pointerId]=t),t.set(e.pageX,e.pageY)}_getSecondPointerPosition(e){const t=e.pointerId===this._pointers[0]?this._pointers[1]:this._pointers[0];return this._pointerPositions[t]}_customWheelEvent(e){const t=e.deltaMode,r={clientX:e.clientX,clientY:e.clientY,deltaY:e.deltaY};switch(t){case 1:r.deltaY*=16;break;case 2:r.deltaY*=100;break}return e.ctrlKey&&!this._controlActive&&(r.deltaY*=10),r}}function ny(n){this.enabled!==!1&&(this._pointers.length===0&&(this.domElement.setPointerCapture(n.pointerId),this.domElement.ownerDocument.addEventListener("pointermove",this._onPointerMove),this.domElement.ownerDocument.addEventListener("pointerup",this._onPointerUp)),!this._isTrackingPointer(n)&&(this._addPointer(n),n.pointerType==="touch"?this._onTouchStart(n):this._onMouseDown(n),this._cursorStyle==="grab"&&(this.domElement.style.cursor="grabbing")))}function iy(n){this.enabled!==!1&&(n.pointerType==="touch"?this._onTouchMove(n):this._onMouseMove(n))}function ry(n){switch(this._removePointer(n),this._pointers.length){case 0:this.domElement.releasePointerCapture(n.pointerId),this.domElement.ownerDocument.removeEventListener("pointermove",this._onPointerMove),this.domElement.ownerDocument.removeEventListener("pointerup",this._onPointerUp),this.dispatchEvent(s0),this.state=St.NONE,this._cursorStyle==="grab"&&(this.domElement.style.cursor="grab");break;case 1:const e=this._pointers[0],t=this._pointerPositions[e];this._onTouchStart({pointerId:e,pageX:t.x,pageY:t.y});break}}function sy(n){let e;switch(n.button){case 0:e=this.mouseButtons.LEFT;break;case 1:e=this.mouseButtons.MIDDLE;break;case 2:e=this.mouseButtons.RIGHT;break;default:e=-1}switch(e){case Ps.DOLLY:if(this.enableZoom===!1)return;this._handleMouseDownDolly(n),this.state=St.DOLLY;break;case Ps.ROTATE:if(n.ctrlKey||n.metaKey||n.shiftKey){if(this.enablePan===!1)return;this._handleMouseDownPan(n),this.state=St.PAN}else{if(this.enableRotate===!1)return;this._handleMouseDownRotate(n),this.state=St.ROTATE}break;case Ps.PAN:if(n.ctrlKey||n.metaKey||n.shiftKey){if(this.enableRotate===!1)return;this._handleMouseDownRotate(n),this.state=St.ROTATE}else{if(this.enablePan===!1)return;this._handleMouseDownPan(n),this.state=St.PAN}break;default:this.state=St.NONE}this.state!==St.NONE&&this.dispatchEvent(tf)}function ay(n){switch(this.state){case St.ROTATE:if(this.enableRotate===!1)return;this._handleMouseMoveRotate(n);break;case St.DOLLY:if(this.enableZoom===!1)return;this._handleMouseMoveDolly(n);break;case St.PAN:if(this.enablePan===!1)return;this._handleMouseMovePan(n);break}}function oy(n){this.enabled===!1||this.enableZoom===!1||this.state!==St.NONE||(n.preventDefault(),this.dispatchEvent(tf),this._handleMouseWheel(this._customWheelEvent(n)),this.dispatchEvent(s0))}function ly(n){this.enabled!==!1&&this._handleKeyDown(n)}function cy(n){switch(this._trackPointer(n),this._pointers.length){case 1:switch(this.touches.ONE){case As.ROTATE:if(this.enableRotate===!1)return;this._handleTouchStartRotate(n),this.state=St.TOUCH_ROTATE;break;case As.PAN:if(this.enablePan===!1)return;this._handleTouchStartPan(n),this.state=St.TOUCH_PAN;break;default:this.state=St.NONE}break;case 2:switch(this.touches.TWO){case As.DOLLY_PAN:if(this.enableZoom===!1&&this.enablePan===!1)return;this._handleTouchStartDollyPan(n),this.state=St.TOUCH_DOLLY_PAN;break;case As.DOLLY_ROTATE:if(this.enableZoom===!1&&this.enableRotate===!1)return;this._handleTouchStartDollyRotate(n),this.state=St.TOUCH_DOLLY_ROTATE;break;default:this.state=St.NONE}break;default:this.state=St.NONE}this.state!==St.NONE&&this.dispatchEvent(tf)}function uy(n){switch(this._trackPointer(n),this.state){case St.TOUCH_ROTATE:if(this.enableRotate===!1)return;this._handleTouchMoveRotate(n),this.update();break;case St.TOUCH_PAN:if(this.enablePan===!1)return;this._handleTouchMovePan(n),this.update();break;case St.TOUCH_DOLLY_PAN:if(this.enableZoom===!1&&this.enablePan===!1)return;this._handleTouchMoveDollyPan(n),this.update();break;case St.TOUCH_DOLLY_ROTATE:if(this.enableZoom===!1&&this.enableRotate===!1)return;this._handleTouchMoveDollyRotate(n),this.update();break;default:this.state=St.NONE}}function hy(n){this.enabled!==!1&&n.preventDefault()}function fy(n){n.key==="Control"&&(this._controlActive=!0,this.domElement.getRootNode().addEventListener("keyup",this._interceptControlUp,{passive:!0,capture:!0}))}function dy(n){n.key==="Control"&&(this._controlActive=!1,this.domElement.getRootNode().removeEventListener("keyup",this._interceptControlUp,{passive:!0,capture:!0}))}function zi(n){if(n===void 0)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return n}function a0(n,e){n.prototype=Object.create(e.prototype),n.prototype.constructor=n,n.__proto__=e}/*!
 * GSAP 3.15.0
 * https://gsap.com
 *
 * @license Copyright 2008-2026, GreenSock. All rights reserved.
 * Subject to the terms at https://gsap.com/standard-license
 * @author: Jack Doyle, jack@greensock.com
*/var Vn={autoSleep:120,force3D:"auto",nullTargetWarn:1,units:{lineHeight:""}},Ba={duration:.5,overwrite:!1,delay:0},nf,un,Ut,Jn=1e8,Et=1/Jn,Mh=Math.PI*2,py=Mh/4,my=0,o0=Math.sqrt,gy=Math.cos,_y=Math.sin,on=function(e){return typeof e=="string"},Gt=function(e){return typeof e=="function"},ji=function(e){return typeof e=="number"},rf=function(e){return typeof e>"u"},Ui=function(e){return typeof e=="object"},Rn=function(e){return e!==!1},sf=function(){return typeof window<"u"},Bo=function(e){return Gt(e)||on(e)},l0=typeof ArrayBuffer=="function"&&ArrayBuffer.isView||function(){},gn=Array.isArray,vy=/random\([^)]+\)/g,xy=/,\s*/g,mp=/(?:-?\.?\d|\.)+/gi,c0=/[-+=.]*\d+[.e\-+]*\d*[e\-+]*\d*/g,Rs=/[-+=.]*\d+[.e-]*\d*[a-z%]*/g,zc=/[-+=.]*\d+\.?\d*(?:e-|e\+)?\d*/gi,u0=/[+-]=-?[.\d]+/,My=/[^,'"\[\]\s]+/gi,Sy=/^[+\-=e\s\d]*\d+[.\d]*([a-z]*|%)\s*$/i,Ft,Si,Sh,af,Xn={},dl={},h0,f0=function(e){return(dl=Gs(e,Xn))&&Un},of=function(e,t){return console.warn("Invalid property",e,"set to",t,"Missing plugin? gsap.registerPlugin()")},ka=function(e,t){return!t&&console.warn(e)},d0=function(e,t){return e&&(Xn[e]=t)&&dl&&(dl[e]=t)||Xn},za=function(){return 0},by={suppressEvents:!0,isStart:!0,kill:!1},Qo={suppressEvents:!0,kill:!1},yy={suppressEvents:!0},lf={},mr=[],bh={},p0,Bn={},Gc={},gp=30,el=[],cf="",uf=function(e){var t=e[0],r,i;if(Ui(t)||Gt(t)||(e=[e]),!(r=(t._gsap||{}).harness)){for(i=el.length;i--&&!el[i].targetTest(t););r=el[i]}for(i=e.length;i--;)e[i]&&(e[i]._gsap||(e[i]._gsap=new N0(e[i],r)))||e.splice(i,1);return e},Hr=function(e){return e._gsap||uf(Qn(e))[0]._gsap},m0=function(e,t,r){return(r=e[t])&&Gt(r)?e[t]():rf(r)&&e.getAttribute&&e.getAttribute(t)||r},Cn=function(e,t){return(e=e.split(",")).forEach(t)||e},Vt=function(e){return Math.round(e*1e5)/1e5||0},It=function(e){return Math.round(e*1e7)/1e7||0},Us=function(e,t){var r=t.charAt(0),i=parseFloat(t.substr(2));return e=parseFloat(e),r==="+"?e+i:r==="-"?e-i:r==="*"?e*i:e/i},Ty=function(e,t){for(var r=t.length,i=0;e.indexOf(t[i])<0&&++i<r;);return i<r},pl=function(){var e=mr.length,t=mr.slice(0),r,i;for(bh={},mr.length=0,r=0;r<e;r++)i=t[r],i&&i._lazy&&(i.render(i._lazy[0],i._lazy[1],!0)._lazy=0)},hf=function(e){return!!(e._initted||e._startAt||e.add)},g0=function(e,t,r,i){mr.length&&!un&&pl(),e.render(t,r,!!(un&&t<0&&hf(e))),mr.length&&!un&&pl()},_0=function(e){var t=parseFloat(e);return(t||t===0)&&(e+"").match(My).length<2?t:on(e)?e.trim():e},v0=function(e){return e},Yn=function(e,t){for(var r in t)r in e||(e[r]=t[r]);return e},Ey=function(e){return function(t,r){for(var i in r)i in t||i==="duration"&&e||i==="ease"||(t[i]=r[i])}},Gs=function(e,t){for(var r in t)e[r]=t[r];return e},_p=function n(e,t){for(var r in t)r!=="__proto__"&&r!=="constructor"&&r!=="prototype"&&(e[r]=Ui(t[r])?n(e[r]||(e[r]={}),t[r]):t[r]);return e},ml=function(e,t){var r={},i;for(i in e)i in t||(r[i]=e[i]);return r},Ua=function(e){var t=e.parent||Ft,r=e.keyframes?Ey(gn(e.keyframes)):Yn;if(Rn(e.inherit))for(;t;)r(e,t.vars.defaults),t=t.parent||t._dp;return e},wy=function(e,t){for(var r=e.length,i=r===t.length;i&&r--&&e[r]===t[r];);return r<0},x0=function(e,t,r,i,s){var a=e[i],o;if(s)for(o=t[s];a&&a[s]>o;)a=a._prev;return a?(t._next=a._next,a._next=t):(t._next=e[r],e[r]=t),t._next?t._next._prev=t:e[i]=t,t._prev=a,t.parent=t._dp=e,t},Ul=function(e,t,r,i){r===void 0&&(r="_first"),i===void 0&&(i="_last");var s=t._prev,a=t._next;s?s._next=a:e[r]===t&&(e[r]=a),a?a._prev=s:e[i]===t&&(e[i]=s),t._next=t._prev=t.parent=null},xr=function(e,t){e.parent&&(!t||e.parent.autoRemoveChildren)&&e.parent.remove&&e.parent.remove(e),e._act=0},Vr=function(e,t){if(e&&(!t||t._end>e._dur||t._start<0))for(var r=e;r;)r._dirty=1,r=r.parent;return e},Ay=function(e){for(var t=e.parent;t&&t.parent;)t._dirty=1,t.totalDuration(),t=t.parent;return e},yh=function(e,t,r,i){return e._startAt&&(un?e._startAt.revert(Qo):e.vars.immediateRender&&!e.vars.autoRevert||e._startAt.render(t,!0,i))},Ry=function n(e){return!e||e._ts&&n(e.parent)},vp=function(e){return e._repeat?Hs(e._tTime,e=e.duration()+e._rDelay)*e:0},Hs=function(e,t){var r=Math.floor(e=It(e/t));return e&&r===e?r-1:r},gl=function(e,t){return(e-t._start)*t._ts+(t._ts>=0?0:t._dirty?t.totalDuration():t._tDur)},Ll=function(e){return e._end=It(e._start+(e._tDur/Math.abs(e._ts||e._rts||Et)||0))},Il=function(e,t){var r=e._dp;return r&&r.smoothChildTiming&&e._ts&&(e._start=It(r._time-(e._ts>0?t/e._ts:((e._dirty?e.totalDuration():e._tDur)-t)/-e._ts)),Ll(e),r._dirty||Vr(r,e)),e},M0=function(e,t){var r;if((t._time||!t._dur&&t._initted||t._start<e._time&&(t._dur||!t.add))&&(r=gl(e.rawTime(),t),(!t._dur||Za(0,t.totalDuration(),r)-t._tTime>Et)&&t.render(r,!0)),Vr(e,t)._dp&&e._initted&&e._time>=e._dur&&e._ts){if(e._dur<e.duration())for(r=e;r._dp;)r.rawTime()>=0&&r.totalTime(r._tTime),r=r._dp;e._zTime=-Et}},Ei=function(e,t,r,i){return t.parent&&xr(t),t._start=It((ji(r)?r:r||e!==Ft?Zn(e,r,t):e._time)+t._delay),t._end=It(t._start+(t.totalDuration()/Math.abs(t.timeScale())||0)),x0(e,t,"_first","_last",e._sort?"_start":0),Th(t)||(e._recent=t),i||M0(e,t),e._ts<0&&Il(e,e._tTime),e},S0=function(e,t){return(Xn.ScrollTrigger||of("scrollTrigger",t))&&Xn.ScrollTrigger.create(t,e)},b0=function(e,t,r,i,s){if(df(e,t,s),!e._initted)return 1;if(!r&&e._pt&&!un&&(e._dur&&e.vars.lazy!==!1||!e._dur&&e.vars.lazy)&&p0!==zn.frame)return mr.push(e),e._lazy=[s,i],1},Cy=function n(e){var t=e.parent;return t&&t._ts&&t._initted&&!t._lock&&(t.rawTime()<0||n(t))},Th=function(e){var t=e.data;return t==="isFromStart"||t==="isStart"},Py=function(e,t,r,i){var s=e.ratio,a=t<0||!t&&(!e._start&&Cy(e)&&!(!e._initted&&Th(e))||(e._ts<0||e._dp._ts<0)&&!Th(e))?0:1,o=e._rDelay,l=0,c,u,f;if(o&&e._repeat&&(l=Za(0,e._tDur,t),u=Hs(l,o),e._yoyo&&u&1&&(a=1-a),u!==Hs(e._tTime,o)&&(s=1-a,e.vars.repeatRefresh&&e._initted&&e.invalidate())),a!==s||un||i||e._zTime===Et||!t&&e._zTime){if(!e._initted&&b0(e,t,i,r,l))return;for(f=e._zTime,e._zTime=t||(r?Et:0),r||(r=t&&!f),e.ratio=a,e._from&&(a=1-a),e._time=0,e._tTime=l,c=e._pt;c;)c.r(a,c.d),c=c._next;t<0&&yh(e,t,r,!0),e._onUpdate&&!r&&Gn(e,"onUpdate"),l&&e._repeat&&!r&&e.parent&&Gn(e,"onRepeat"),(t>=e._tDur||t<0)&&e.ratio===a&&(a&&xr(e,1),!r&&!un&&(Gn(e,a?"onComplete":"onReverseComplete",!0),e._prom&&e._prom()))}else e._zTime||(e._zTime=t)},Dy=function(e,t,r){var i;if(r>t)for(i=e._first;i&&i._start<=r;){if(i.data==="isPause"&&i._start>t)return i;i=i._next}else for(i=e._last;i&&i._start>=r;){if(i.data==="isPause"&&i._start<t)return i;i=i._prev}},Vs=function(e,t,r,i){var s=e._repeat,a=It(t)||0,o=e._tTime/e._tDur;return o&&!i&&(e._time*=a/e._dur),e._dur=a,e._tDur=s?s<0?1e10:It(a*(s+1)+e._rDelay*s):a,o>0&&!i&&Il(e,e._tTime=e._tDur*o),e.parent&&Ll(e),r||Vr(e.parent,e),e},xp=function(e){return e instanceof An?Vr(e):Vs(e,e._dur)},Uy={_start:0,endTime:za,totalDuration:za},Zn=function n(e,t,r){var i=e.labels,s=e._recent||Uy,a=e.duration()>=Jn?s.endTime(!1):e._dur,o,l,c;return on(t)&&(isNaN(t)||t in i)?(l=t.charAt(0),c=t.substr(-1)==="%",o=t.indexOf("="),l==="<"||l===">"?(o>=0&&(t=t.replace(/=/,"")),(l==="<"?s._start:s.endTime(s._repeat>=0))+(parseFloat(t.substr(1))||0)*(c?(o<0?s:r).totalDuration()/100:1)):o<0?(t in i||(i[t]=a),i[t]):(l=parseFloat(t.charAt(o-1)+t.substr(o+1)),c&&r&&(l=l/100*(gn(r)?r[0]:r).totalDuration()),o>1?n(e,t.substr(0,o-1),r)+l:a+l)):t==null?a:+t},La=function(e,t,r){var i=ji(t[1]),s=(i?2:1)+(e<2?0:1),a=t[s],o,l;if(i&&(a.duration=t[1]),a.parent=r,e){for(o=a,l=r;l&&!("immediateRender"in o);)o=l.vars.defaults||{},l=Rn(l.vars.inherit)&&l.parent;a.immediateRender=Rn(o.immediateRender),e<2?a.runBackwards=1:a.startAt=t[s-1]}return new Xt(t[0],a,t[s+1])},Tr=function(e,t){return e||e===0?t(e):t},Za=function(e,t,r){return r<e?e:r>t?t:r},pn=function(e,t){return!on(e)||!(t=Sy.exec(e))?"":t[1]},Ly=function(e,t,r){return Tr(r,function(i){return Za(e,t,i)})},Eh=[].slice,y0=function(e,t){return e&&Ui(e)&&"length"in e&&(!t&&!e.length||e.length-1 in e&&Ui(e[0]))&&!e.nodeType&&e!==Si},Iy=function(e,t,r){return r===void 0&&(r=[]),e.forEach(function(i){var s;return on(i)&&!t||y0(i,1)?(s=r).push.apply(s,Qn(i)):r.push(i)})||r},Qn=function(e,t,r){return Ut&&!t&&Ut.selector?Ut.selector(e):on(e)&&!r&&(Sh||!Ws())?Eh.call((t||af).querySelectorAll(e),0):gn(e)?Iy(e,r):y0(e)?Eh.call(e,0):e?[e]:[]},wh=function(e){return e=Qn(e)[0]||ka("Invalid scope")||{},function(t){var r=e.current||e.nativeElement||e;return Qn(t,r.querySelectorAll?r:r===e?ka("Invalid scope")||af.createElement("div"):e)}},T0=function(e){return e.sort(function(){return .5-Math.random()})},E0=function(e){if(Gt(e))return e;var t=Ui(e)?e:{each:e},r=Wr(t.ease),i=t.from||0,s=parseFloat(t.base)||0,a={},o=i>0&&i<1,l=isNaN(i)||o,c=t.axis,u=i,f=i;return on(i)?u=f={center:.5,edges:.5,end:1}[i]||0:!o&&l&&(u=i[0],f=i[1]),function(h,d,m){var g=(m||t).length,p=a[g],_,M,y,v,S,b,E,x,w;if(!p){if(w=t.grid==="auto"?0:(t.grid||[1,Jn])[1],!w){for(E=-Jn;E<(E=m[w++].getBoundingClientRect().left)&&w<g;);w<g&&w--}for(p=a[g]=[],_=l?Math.min(w,g)*u-.5:i%w,M=w===Jn?0:l?g*f/w-.5:i/w|0,E=0,x=Jn,b=0;b<g;b++)y=b%w-_,v=M-(b/w|0),p[b]=S=c?Math.abs(c==="y"?v:y):o0(y*y+v*v),S>E&&(E=S),S<x&&(x=S);i==="random"&&T0(p),p.max=E-x,p.min=x,p.v=g=(parseFloat(t.amount)||parseFloat(t.each)*(w>g?g-1:c?c==="y"?g/w:w:Math.max(w,g/w))||0)*(i==="edges"?-1:1),p.b=g<0?s-g:s,p.u=pn(t.amount||t.each)||0,r=r&&g<0?qy(r):r}return g=(p[h]-p.min)/p.max||0,It(p.b+(r?r(g):g)*p.v)+p.u}},Ah=function(e){var t=Math.pow(10,((e+"").split(".")[1]||"").length);return function(r){var i=It(Math.round(parseFloat(r)/e)*e*t);return(i-i%1)/t+(ji(r)?0:pn(r))}},w0=function(e,t){var r=gn(e),i,s;return!r&&Ui(e)&&(i=r=e.radius||Jn,e.values?(e=Qn(e.values),(s=!ji(e[0]))&&(i*=i)):e=Ah(e.increment)),Tr(t,r?Gt(e)?function(a){return s=e(a),Math.abs(s-a)<=i?s:a}:function(a){for(var o=parseFloat(s?a.x:a),l=parseFloat(s?a.y:0),c=Jn,u=0,f=e.length,h,d;f--;)s?(h=e[f].x-o,d=e[f].y-l,h=h*h+d*d):h=Math.abs(e[f]-o),h<c&&(c=h,u=f);return u=!i||c<=i?e[u]:a,s||u===a||ji(a)?u:u+pn(a)}:Ah(e))},A0=function(e,t,r,i){return Tr(gn(e)?!t:r===!0?!!(r=0):!i,function(){return gn(e)?e[~~(Math.random()*e.length)]:(r=r||1e-5)&&(i=r<1?Math.pow(10,(r+"").length-2):1)&&Math.floor(Math.round((e-r/2+Math.random()*(t-e+r*.99))/r)*r*i)/i})},Fy=function(){for(var e=arguments.length,t=new Array(e),r=0;r<e;r++)t[r]=arguments[r];return function(i){return t.reduce(function(s,a){return a(s)},i)}},Ny=function(e,t){return function(r){return e(parseFloat(r))+(t||pn(r))}},Oy=function(e,t,r){return C0(e,t,0,1,r)},R0=function(e,t,r){return Tr(r,function(i){return e[~~t(i)]})},By=function n(e,t,r){var i=t-e;return gn(e)?R0(e,n(0,e.length),t):Tr(r,function(s){return(i+(s-e)%i)%i+e})},ky=function n(e,t,r){var i=t-e,s=i*2;return gn(e)?R0(e,n(0,e.length-1),t):Tr(r,function(a){return a=(s+(a-e)%s)%s||0,e+(a>i?s-a:a)})},Ga=function(e){return e.replace(vy,function(t){var r=t.indexOf("[")+1,i=t.substring(r||7,r?t.indexOf("]"):t.length-1).split(xy);return A0(r?i:+i[0],r?0:+i[1],+i[2]||1e-5)})},C0=function(e,t,r,i,s){var a=t-e,o=i-r;return Tr(s,function(l){return r+((l-e)/a*o||0)})},zy=function n(e,t,r,i){var s=isNaN(e+t)?0:function(d){return(1-d)*e+d*t};if(!s){var a=on(e),o={},l,c,u,f,h;if(r===!0&&(i=1)&&(r=null),a)e={p:e},t={p:t};else if(gn(e)&&!gn(t)){for(u=[],f=e.length,h=f-2,c=1;c<f;c++)u.push(n(e[c-1],e[c]));f--,s=function(m){m*=f;var g=Math.min(h,~~m);return u[g](m-g)},r=t}else i||(e=Gs(gn(e)?[]:{},e));if(!u){for(l in t)ff.call(o,e,l,"get",t[l]);s=function(m){return gf(m,o)||(a?e.p:e)}}}return Tr(r,s)},Mp=function(e,t,r){var i=e.labels,s=Jn,a,o,l;for(a in i)o=i[a]-t,o<0==!!r&&o&&s>(o=Math.abs(o))&&(l=a,s=o);return l},Gn=function(e,t,r){var i=e.vars,s=i[t],a=Ut,o=e._ctx,l,c,u;if(s)return l=i[t+"Params"],c=i.callbackScope||e,r&&mr.length&&pl(),o&&(Ut=o),u=l?s.apply(c,l):s.call(c),Ut=a,u},Aa=function(e){return xr(e),e.scrollTrigger&&e.scrollTrigger.kill(!!un),e.progress()<1&&Gn(e,"onInterrupt"),e},Cs,P0=[],D0=function(e){if(e)if(e=!e.name&&e.default||e,sf()||e.headless){var t=e.name,r=Gt(e),i=t&&!r&&e.init?function(){this._props=[]}:e,s={init:za,render:gf,add:ff,kill:iT,modifier:nT,rawVars:0},a={targetTest:0,get:0,getSetter:mf,aliases:{},register:0};if(Ws(),e!==i){if(Bn[t])return;Yn(i,Yn(ml(e,s),a)),Gs(i.prototype,Gs(s,ml(e,a))),Bn[i.prop=t]=i,e.targetTest&&(el.push(i),lf[t]=1),t=(t==="css"?"CSS":t.charAt(0).toUpperCase()+t.substr(1))+"Plugin"}d0(t,i),e.register&&e.register(Un,i,Pn)}else P0.push(e)},Tt=255,Ra={aqua:[0,Tt,Tt],lime:[0,Tt,0],silver:[192,192,192],black:[0,0,0],maroon:[128,0,0],teal:[0,128,128],blue:[0,0,Tt],navy:[0,0,128],white:[Tt,Tt,Tt],olive:[128,128,0],yellow:[Tt,Tt,0],orange:[Tt,165,0],gray:[128,128,128],purple:[128,0,128],green:[0,128,0],red:[Tt,0,0],pink:[Tt,192,203],cyan:[0,Tt,Tt],transparent:[Tt,Tt,Tt,0]},Hc=function(e,t,r){return e+=e<0?1:e>1?-1:0,(e*6<1?t+(r-t)*e*6:e<.5?r:e*3<2?t+(r-t)*(2/3-e)*6:t)*Tt+.5|0},U0=function(e,t,r){var i=e?ji(e)?[e>>16,e>>8&Tt,e&Tt]:0:Ra.black,s,a,o,l,c,u,f,h,d,m;if(!i){if(e.substr(-1)===","&&(e=e.substr(0,e.length-1)),Ra[e])i=Ra[e];else if(e.charAt(0)==="#"){if(e.length<6&&(s=e.charAt(1),a=e.charAt(2),o=e.charAt(3),e="#"+s+s+a+a+o+o+(e.length===5?e.charAt(4)+e.charAt(4):"")),e.length===9)return i=parseInt(e.substr(1,6),16),[i>>16,i>>8&Tt,i&Tt,parseInt(e.substr(7),16)/255];e=parseInt(e.substr(1),16),i=[e>>16,e>>8&Tt,e&Tt]}else if(e.substr(0,3)==="hsl"){if(i=m=e.match(mp),!t)l=+i[0]%360/360,c=+i[1]/100,u=+i[2]/100,a=u<=.5?u*(c+1):u+c-u*c,s=u*2-a,i.length>3&&(i[3]*=1),i[0]=Hc(l+1/3,s,a),i[1]=Hc(l,s,a),i[2]=Hc(l-1/3,s,a);else if(~e.indexOf("="))return i=e.match(c0),r&&i.length<4&&(i[3]=1),i}else i=e.match(mp)||Ra.transparent;i=i.map(Number)}return t&&!m&&(s=i[0]/Tt,a=i[1]/Tt,o=i[2]/Tt,f=Math.max(s,a,o),h=Math.min(s,a,o),u=(f+h)/2,f===h?l=c=0:(d=f-h,c=u>.5?d/(2-f-h):d/(f+h),l=f===s?(a-o)/d+(a<o?6:0):f===a?(o-s)/d+2:(s-a)/d+4,l*=60),i[0]=~~(l+.5),i[1]=~~(c*100+.5),i[2]=~~(u*100+.5)),r&&i.length<4&&(i[3]=1),i},L0=function(e){var t=[],r=[],i=-1;return e.split(gr).forEach(function(s){var a=s.match(Rs)||[];t.push.apply(t,a),r.push(i+=a.length+1)}),t.c=r,t},Sp=function(e,t,r){var i="",s=(e+i).match(gr),a=t?"hsla(":"rgba(",o=0,l,c,u,f;if(!s)return e;if(s=s.map(function(h){return(h=U0(h,t,1))&&a+(t?h[0]+","+h[1]+"%,"+h[2]+"%,"+h[3]:h.join(","))+")"}),r&&(u=L0(e),l=r.c,l.join(i)!==u.c.join(i)))for(c=e.replace(gr,"1").split(Rs),f=c.length-1;o<f;o++)i+=c[o]+(~l.indexOf(o)?s.shift()||a+"0,0,0,0)":(u.length?u:s.length?s:r).shift());if(!c)for(c=e.split(gr),f=c.length-1;o<f;o++)i+=c[o]+s[o];return i+c[f]},gr=(function(){var n="(?:\\b(?:(?:rgb|rgba|hsl|hsla)\\(.+?\\))|\\B#(?:[0-9a-f]{3,4}){1,2}\\b",e;for(e in Ra)n+="|"+e+"\\b";return new RegExp(n+")","gi")})(),Gy=/hsl[a]?\(/,I0=function(e){var t=e.join(" "),r;if(gr.lastIndex=0,gr.test(t))return r=Gy.test(t),e[1]=Sp(e[1],r),e[0]=Sp(e[0],r,L0(e[1])),!0},Ha,zn=(function(){var n=Date.now,e=500,t=33,r=n(),i=r,s=1e3/240,a=s,o=[],l,c,u,f,h,d,m=function g(p){var _=n()-i,M=p===!0,y,v,S,b;if((_>e||_<0)&&(r+=_-t),i+=_,S=i-r,y=S-a,(y>0||M)&&(b=++f.frame,h=S-f.time*1e3,f.time=S=S/1e3,a+=y+(y>=s?4:s-y),v=1),M||(l=c(g)),v)for(d=0;d<o.length;d++)o[d](S,h,b,p)};return f={time:0,frame:0,tick:function(){m(!0)},deltaRatio:function(p){return h/(1e3/(p||60))},wake:function(){h0&&(!Sh&&sf()&&(Si=Sh=window,af=Si.document||{},Xn.gsap=Un,(Si.gsapVersions||(Si.gsapVersions=[])).push(Un.version),f0(dl||Si.GreenSockGlobals||!Si.gsap&&Si||{}),P0.forEach(D0)),u=typeof requestAnimationFrame<"u"&&requestAnimationFrame,l&&f.sleep(),c=u||function(p){return setTimeout(p,a-f.time*1e3+1|0)},Ha=1,m(2))},sleep:function(){(u?cancelAnimationFrame:clearTimeout)(l),Ha=0,c=za},lagSmoothing:function(p,_){e=p||1/0,t=Math.min(_||33,e)},fps:function(p){s=1e3/(p||240),a=f.time*1e3+s},add:function(p,_,M){var y=_?function(v,S,b,E){p(v,S,b,E),f.remove(y)}:p;return f.remove(p),o[M?"unshift":"push"](y),Ws(),y},remove:function(p,_){~(_=o.indexOf(p))&&o.splice(_,1)&&d>=_&&d--},_listeners:o},f})(),Ws=function(){return!Ha&&zn.wake()},ht={},Hy=/^[\d.\-M][\d.\-,\s]/,Vy=/["']/g,Wy=function(e){for(var t={},r=e.substr(1,e.length-3).split(":"),i=r[0],s=1,a=r.length,o,l,c;s<a;s++)l=r[s],o=s!==a-1?l.lastIndexOf(","):l.length,c=l.substr(0,o),t[i]=isNaN(c)?c.replace(Vy,"").trim():+c,i=l.substr(o+1).trim();return t},Xy=function(e){var t=e.indexOf("(")+1,r=e.indexOf(")"),i=e.indexOf("(",t);return e.substring(t,~i&&i<r?e.indexOf(")",r+1):r)},Yy=function(e){var t=(e+"").split("("),r=ht[t[0]];return r&&t.length>1&&r.config?r.config.apply(null,~e.indexOf("{")?[Wy(t[1])]:Xy(e).split(",").map(_0)):ht._CE&&Hy.test(e)?ht._CE("",e):r},qy=function(e){return function(t){return 1-e(1-t)}},Wr=function(e,t){return e&&(Gt(e)?e:ht[e]||Yy(e))||t},Jr=function(e,t,r,i){r===void 0&&(r=function(l){return 1-t(1-l)}),i===void 0&&(i=function(l){return l<.5?t(l*2)/2:1-t((1-l)*2)/2});var s={easeIn:t,easeOut:r,easeInOut:i},a;return Cn(e,function(o){ht[o]=Xn[o]=s,ht[a=o.toLowerCase()]=r;for(var l in s)ht[a+(l==="easeIn"?".in":l==="easeOut"?".out":".inOut")]=ht[o+"."+l]=s[l]}),s},F0=function(e){return function(t){return t<.5?(1-e(1-t*2))/2:.5+e((t-.5)*2)/2}},Vc=function n(e,t,r){var i=t>=1?t:1,s=(r||(e?.3:.45))/(t<1?t:1),a=s/Mh*(Math.asin(1/i)||0),o=function(u){return u===1?1:i*Math.pow(2,-10*u)*_y((u-a)*s)+1},l=e==="out"?o:e==="in"?function(c){return 1-o(1-c)}:F0(o);return s=Mh/s,l.config=function(c,u){return n(e,c,u)},l},Wc=function n(e,t){t===void 0&&(t=1.70158);var r=function(a){return a?--a*a*((t+1)*a+t)+1:0},i=e==="out"?r:e==="in"?function(s){return 1-r(1-s)}:F0(r);return i.config=function(s){return n(e,s)},i};Cn("Linear,Quad,Cubic,Quart,Quint,Strong",function(n,e){var t=e<5?e+1:e;Jr(n+",Power"+(t-1),e?function(r){return Math.pow(r,t)}:function(r){return r},function(r){return 1-Math.pow(1-r,t)},function(r){return r<.5?Math.pow(r*2,t)/2:1-Math.pow((1-r)*2,t)/2})});ht.Linear.easeNone=ht.none=ht.Linear.easeIn;Jr("Elastic",Vc("in"),Vc("out"),Vc());(function(n,e){var t=1/e,r=2*t,i=2.5*t,s=function(o){return o<t?n*o*o:o<r?n*Math.pow(o-1.5/e,2)+.75:o<i?n*(o-=2.25/e)*o+.9375:n*Math.pow(o-2.625/e,2)+.984375};Jr("Bounce",function(a){return 1-s(1-a)},s)})(7.5625,2.75);Jr("Expo",function(n){return Math.pow(2,10*(n-1))*n+n*n*n*n*n*n*(1-n)});Jr("Circ",function(n){return-(o0(1-n*n)-1)});Jr("Sine",function(n){return n===1?1:-gy(n*py)+1});Jr("Back",Wc("in"),Wc("out"),Wc());ht.SteppedEase=ht.steps=Xn.SteppedEase={config:function(e,t){e===void 0&&(e=1);var r=1/e,i=e+(t?0:1),s=t?1:0,a=1-Et;return function(o){return((i*Za(0,a,o)|0)+s)*r}}};Ba.ease=ht["quad.out"];Cn("onComplete,onUpdate,onStart,onRepeat,onReverseComplete,onInterrupt",function(n){return cf+=n+","+n+"Params,"});var N0=function(e,t){this.id=my++,e._gsap=this,this.target=e,this.harness=t,this.get=t?t.get:m0,this.set=t?t.getSetter:mf},Va=(function(){function n(t){this.vars=t,this._delay=+t.delay||0,(this._repeat=t.repeat===1/0?-2:t.repeat||0)&&(this._rDelay=t.repeatDelay||0,this._yoyo=!!t.yoyo||!!t.yoyoEase),this._ts=1,Vs(this,+t.duration,1,1),this.data=t.data,Ut&&(this._ctx=Ut,Ut.data.push(this)),Ha||zn.wake()}var e=n.prototype;return e.delay=function(r){return r||r===0?(this.parent&&this.parent.smoothChildTiming&&this.startTime(this._start+r-this._delay),this._delay=r,this):this._delay},e.duration=function(r){return arguments.length?this.totalDuration(this._repeat>0?r+(r+this._rDelay)*this._repeat:r):this.totalDuration()&&this._dur},e.totalDuration=function(r){return arguments.length?(this._dirty=0,Vs(this,this._repeat<0?r:(r-this._repeat*this._rDelay)/(this._repeat+1))):this._tDur},e.totalTime=function(r,i){if(Ws(),!arguments.length)return this._tTime;var s=this._dp;if(s&&s.smoothChildTiming&&this._ts){for(Il(this,r),!s._dp||s.parent||M0(s,this);s&&s.parent;)s.parent._time!==s._start+(s._ts>=0?s._tTime/s._ts:(s.totalDuration()-s._tTime)/-s._ts)&&s.totalTime(s._tTime,!0),s=s.parent;!this.parent&&this._dp.autoRemoveChildren&&(this._ts>0&&r<this._tDur||this._ts<0&&r>0||!this._tDur&&!r)&&Ei(this._dp,this,this._start-this._delay)}return(this._tTime!==r||!this._dur&&!i||this._initted&&Math.abs(this._zTime)===Et||!this._initted&&this._dur&&r||!r&&!this._initted&&(this.add||this._ptLookup))&&(this._ts||(this._pTime=r),g0(this,r,i)),this},e.time=function(r,i){return arguments.length?this.totalTime(Math.min(this.totalDuration(),r+vp(this))%(this._dur+this._rDelay)||(r?this._dur:0),i):this._time},e.totalProgress=function(r,i){return arguments.length?this.totalTime(this.totalDuration()*r,i):this.totalDuration()?Math.min(1,this._tTime/this._tDur):this.rawTime()>=0&&this._initted?1:0},e.progress=function(r,i){return arguments.length?this.totalTime(this.duration()*(this._yoyo&&!(this.iteration()&1)?1-r:r)+vp(this),i):this.duration()?Math.min(1,this._time/this._dur):this.rawTime()>0?1:0},e.iteration=function(r,i){var s=this.duration()+this._rDelay;return arguments.length?this.totalTime(this._time+(r-1)*s,i):this._repeat?Hs(this._tTime,s)+1:1},e.timeScale=function(r,i){if(!arguments.length)return this._rts===-Et?0:this._rts;if(this._rts===r)return this;var s=this.parent&&this._ts?gl(this.parent._time,this):this._tTime;return this._rts=+r||0,this._ts=this._ps||r===-Et?0:this._rts,this.totalTime(Za(-Math.abs(this._delay),this.totalDuration(),s),i!==!1),Ll(this),Ay(this)},e.paused=function(r){return arguments.length?(this._ps!==r&&(this._ps=r,r?(this._pTime=this._tTime||Math.max(-this._delay,this.rawTime()),this._ts=this._act=0):(Ws(),this._ts=this._rts,this.totalTime(this.parent&&!this.parent.smoothChildTiming?this.rawTime():this._tTime||this._pTime,this.progress()===1&&Math.abs(this._zTime)!==Et&&(this._tTime-=Et)))),this):this._ps},e.startTime=function(r){if(arguments.length){this._start=It(r);var i=this.parent||this._dp;return i&&(i._sort||!this.parent)&&Ei(i,this,this._start-this._delay),this}return this._start},e.endTime=function(r){return this._start+(Rn(r)?this.totalDuration():this.duration())/Math.abs(this._ts||1)},e.rawTime=function(r){var i=this.parent||this._dp;return i?r&&(!this._ts||this._repeat&&this._time&&this.totalProgress()<1)?this._tTime%(this._dur+this._rDelay):this._ts?gl(i.rawTime(r),this):this._tTime:this._tTime},e.revert=function(r){r===void 0&&(r=yy);var i=un;return un=r,hf(this)&&(this.timeline&&this.timeline.revert(r),this.totalTime(-.01,r.suppressEvents)),this.data!=="nested"&&r.kill!==!1&&this.kill(),un=i,this},e.globalTime=function(r){for(var i=this,s=arguments.length?r:i.rawTime();i;)s=i._start+s/(Math.abs(i._ts)||1),i=i._dp;return!this.parent&&this._sat?this._sat.globalTime(r):s},e.repeat=function(r){return arguments.length?(this._repeat=r===1/0?-2:r,xp(this)):this._repeat===-2?1/0:this._repeat},e.repeatDelay=function(r){if(arguments.length){var i=this._time;return this._rDelay=r,xp(this),i?this.time(i):this}return this._rDelay},e.yoyo=function(r){return arguments.length?(this._yoyo=r,this):this._yoyo},e.seek=function(r,i){return this.totalTime(Zn(this,r),Rn(i))},e.restart=function(r,i){return this.play().totalTime(r?-this._delay:0,Rn(i)),this._dur||(this._zTime=-Et),this},e.play=function(r,i){return r!=null&&this.seek(r,i),this.reversed(!1).paused(!1)},e.reverse=function(r,i){return r!=null&&this.seek(r||this.totalDuration(),i),this.reversed(!0).paused(!1)},e.pause=function(r,i){return r!=null&&this.seek(r,i),this.paused(!0)},e.resume=function(){return this.paused(!1)},e.reversed=function(r){return arguments.length?(!!r!==this.reversed()&&this.timeScale(-this._rts||(r?-Et:0)),this):this._rts<0},e.invalidate=function(){return this._initted=this._act=0,this._zTime=-Et,this},e.isActive=function(){var r=this.parent||this._dp,i=this._start,s;return!!(!r||this._ts&&this._initted&&r.isActive()&&(s=r.rawTime(!0))>=i&&s<this.endTime(!0)-Et)},e.eventCallback=function(r,i,s){var a=this.vars;return arguments.length>1?(i?(a[r]=i,s&&(a[r+"Params"]=s),r==="onUpdate"&&(this._onUpdate=i)):delete a[r],this):a[r]},e.then=function(r){var i=this,s=i._prom;return new Promise(function(a){var o=Gt(r)?r:v0,l=function(){var u=i.then;i.then=null,s&&s(),Gt(o)&&(o=o(i))&&(o.then||o===i)&&(i.then=u),a(o),i.then=u};i._initted&&i.totalProgress()===1&&i._ts>=0||!i._tTime&&i._ts<0?l():i._prom=l})},e.kill=function(){Aa(this)},n})();Yn(Va.prototype,{_time:0,_start:0,_end:0,_tTime:0,_tDur:0,_dirty:0,_repeat:0,_yoyo:!1,parent:null,_initted:!1,_rDelay:0,_ts:1,_dp:0,ratio:0,_zTime:-Et,_prom:0,_ps:!1,_rts:1});var An=(function(n){a0(e,n);function e(r,i){var s;return r===void 0&&(r={}),s=n.call(this,r)||this,s.labels={},s.smoothChildTiming=!!r.smoothChildTiming,s.autoRemoveChildren=!!r.autoRemoveChildren,s._sort=Rn(r.sortChildren),Ft&&Ei(r.parent||Ft,zi(s),i),r.reversed&&s.reverse(),r.paused&&s.paused(!0),r.scrollTrigger&&S0(zi(s),r.scrollTrigger),s}var t=e.prototype;return t.to=function(i,s,a){return La(0,arguments,this),this},t.from=function(i,s,a){return La(1,arguments,this),this},t.fromTo=function(i,s,a,o){return La(2,arguments,this),this},t.set=function(i,s,a){return s.duration=0,s.parent=this,Ua(s).repeatDelay||(s.repeat=0),s.immediateRender=!!s.immediateRender,new Xt(i,s,Zn(this,a),1),this},t.call=function(i,s,a){return Ei(this,Xt.delayedCall(0,i,s),a)},t.staggerTo=function(i,s,a,o,l,c,u){return a.duration=s,a.stagger=a.stagger||o,a.onComplete=c,a.onCompleteParams=u,a.parent=this,new Xt(i,a,Zn(this,l)),this},t.staggerFrom=function(i,s,a,o,l,c,u){return a.runBackwards=1,Ua(a).immediateRender=Rn(a.immediateRender),this.staggerTo(i,s,a,o,l,c,u)},t.staggerFromTo=function(i,s,a,o,l,c,u,f){return o.startAt=a,Ua(o).immediateRender=Rn(o.immediateRender),this.staggerTo(i,s,o,l,c,u,f)},t.render=function(i,s,a){var o=this._time,l=this._dirty?this.totalDuration():this._tDur,c=this._dur,u=i<=0?0:It(i),f=this._zTime<0!=i<0&&(this._initted||!c),h,d,m,g,p,_,M,y,v,S,b,E;if(this!==Ft&&u>l&&i>=0&&(u=l),u!==this._tTime||a||f){if(o!==this._time&&c&&(u+=this._time-o,i+=this._time-o),h=u,v=this._start,y=this._ts,_=!y,f&&(c||(o=this._zTime),(i||!s)&&(this._zTime=i)),this._repeat){if(b=this._yoyo,p=c+this._rDelay,this._repeat<-1&&i<0)return this.totalTime(p*100+i,s,a);if(h=It(u%p),u===l?(g=this._repeat,h=c):(S=It(u/p),g=~~S,g&&g===S&&(h=c,g--),h>c&&(h=c)),S=Hs(this._tTime,p),!o&&this._tTime&&S!==g&&this._tTime-S*p-this._dur<=0&&(S=g),b&&g&1&&(h=c-h,E=1),g!==S&&!this._lock){var x=b&&S&1,w=x===(b&&g&1);if(g<S&&(x=!x),o=x?0:u%c?c:u,this._lock=1,this.render(o||(E?0:It(g*p)),s,!c)._lock=0,this._tTime=u,!s&&this.parent&&Gn(this,"onRepeat"),this.vars.repeatRefresh&&!E&&(this.invalidate()._lock=1,S=g),o&&o!==this._time||_!==!this._ts||this.vars.onRepeat&&!this.parent&&!this._act)return this;if(c=this._dur,l=this._tDur,w&&(this._lock=2,o=x?c:-1e-4,this.render(o,!0),this.vars.repeatRefresh&&!E&&this.invalidate()),this._lock=0,!this._ts&&!_)return this}}if(this._hasPause&&!this._forcing&&this._lock<2&&(M=Dy(this,It(o),It(h)),M&&(u-=h-(h=M._start))),this._tTime=u,this._time=h,this._act=!!y,this._initted||(this._onUpdate=this.vars.onUpdate,this._initted=1,this._zTime=i,o=0),!o&&u&&c&&!s&&!S&&(Gn(this,"onStart"),this._tTime!==u))return this;if(h>=o&&i>=0)for(d=this._first;d;){if(m=d._next,(d._act||h>=d._start)&&d._ts&&M!==d){if(d.parent!==this)return this.render(i,s,a);if(d.render(d._ts>0?(h-d._start)*d._ts:(d._dirty?d.totalDuration():d._tDur)+(h-d._start)*d._ts,s,a),h!==this._time||!this._ts&&!_){M=0,m&&(u+=this._zTime=-Et);break}}d=m}else{d=this._last;for(var R=i<0?i:h;d;){if(m=d._prev,(d._act||R<=d._end)&&d._ts&&M!==d){if(d.parent!==this)return this.render(i,s,a);if(d.render(d._ts>0?(R-d._start)*d._ts:(d._dirty?d.totalDuration():d._tDur)+(R-d._start)*d._ts,s,a||un&&hf(d)),h!==this._time||!this._ts&&!_){M=0,m&&(u+=this._zTime=R?-Et:Et);break}}d=m}}if(M&&!s&&(this.pause(),M.render(h>=o?0:-Et)._zTime=h>=o?1:-1,this._ts))return this._start=v,Ll(this),this.render(i,s,a);this._onUpdate&&!s&&Gn(this,"onUpdate",!0),(u===l&&this._tTime>=this.totalDuration()||!u&&o)&&(v===this._start||Math.abs(y)!==Math.abs(this._ts))&&(this._lock||((i||!c)&&(u===l&&this._ts>0||!u&&this._ts<0)&&xr(this,1),!s&&!(i<0&&!o)&&(u||o||!l)&&(Gn(this,u===l&&i>=0?"onComplete":"onReverseComplete",!0),this._prom&&!(u<l&&this.timeScale()>0)&&this._prom())))}return this},t.add=function(i,s){var a=this;if(ji(s)||(s=Zn(this,s,i)),!(i instanceof Va)){if(gn(i))return i.forEach(function(o){return a.add(o,s)}),this;if(on(i))return this.addLabel(i,s);if(Gt(i))i=Xt.delayedCall(0,i);else return this}return this!==i?Ei(this,i,s):this},t.getChildren=function(i,s,a,o){i===void 0&&(i=!0),s===void 0&&(s=!0),a===void 0&&(a=!0),o===void 0&&(o=-Jn);for(var l=[],c=this._first;c;)c._start>=o&&(c instanceof Xt?s&&l.push(c):(a&&l.push(c),i&&l.push.apply(l,c.getChildren(!0,s,a)))),c=c._next;return l},t.getById=function(i){for(var s=this.getChildren(1,1,1),a=s.length;a--;)if(s[a].vars.id===i)return s[a]},t.remove=function(i){return on(i)?this.removeLabel(i):Gt(i)?this.killTweensOf(i):(i.parent===this&&Ul(this,i),i===this._recent&&(this._recent=this._last),Vr(this))},t.totalTime=function(i,s){return arguments.length?(this._forcing=1,!this._dp&&this._ts&&(this._start=It(zn.time-(this._ts>0?i/this._ts:(this.totalDuration()-i)/-this._ts))),n.prototype.totalTime.call(this,i,s),this._forcing=0,this):this._tTime},t.addLabel=function(i,s){return this.labels[i]=Zn(this,s),this},t.removeLabel=function(i){return delete this.labels[i],this},t.addPause=function(i,s,a){var o=Xt.delayedCall(0,s||za,a);return o.data="isPause",this._hasPause=1,Ei(this,o,Zn(this,i))},t.removePause=function(i){var s=this._first;for(i=Zn(this,i);s;)s._start===i&&s.data==="isPause"&&xr(s),s=s._next},t.killTweensOf=function(i,s,a){for(var o=this.getTweensOf(i,a),l=o.length;l--;)hr!==o[l]&&o[l].kill(i,s);return this},t.getTweensOf=function(i,s){for(var a=[],o=Qn(i),l=this._first,c=ji(s),u;l;)l instanceof Xt?Ty(l._targets,o)&&(c?(!hr||l._initted&&l._ts)&&l.globalTime(0)<=s&&l.globalTime(l.totalDuration())>s:!s||l.isActive())&&a.push(l):(u=l.getTweensOf(o,s)).length&&a.push.apply(a,u),l=l._next;return a},t.tweenTo=function(i,s){s=s||{};var a=this,o=Zn(a,i),l=s,c=l.startAt,u=l.onStart,f=l.onStartParams,h=l.immediateRender,d,m=Xt.to(a,Yn({ease:s.ease||"none",lazy:!1,immediateRender:!1,time:o,overwrite:"auto",duration:s.duration||Math.abs((o-(c&&"time"in c?c.time:a._time))/a.timeScale())||Et,onStart:function(){if(a.pause(),!d){var p=s.duration||Math.abs((o-(c&&"time"in c?c.time:a._time))/a.timeScale());m._dur!==p&&Vs(m,p,0,1).render(m._time,!0,!0),d=1}u&&u.apply(m,f||[])}},s));return h?m.render(0):m},t.tweenFromTo=function(i,s,a){return this.tweenTo(s,Yn({startAt:{time:Zn(this,i)}},a))},t.recent=function(){return this._recent},t.nextLabel=function(i){return i===void 0&&(i=this._time),Mp(this,Zn(this,i))},t.previousLabel=function(i){return i===void 0&&(i=this._time),Mp(this,Zn(this,i),1)},t.currentLabel=function(i){return arguments.length?this.seek(i,!0):this.previousLabel(this._time+Et)},t.shiftChildren=function(i,s,a){a===void 0&&(a=0);var o=this._first,l=this.labels,c;for(i=It(i);o;)o._start>=a&&(o._start+=i,o._end+=i),o=o._next;if(s)for(c in l)l[c]>=a&&(l[c]+=i);return Vr(this)},t.invalidate=function(i){var s=this._first;for(this._lock=0;s;)s.invalidate(i),s=s._next;return n.prototype.invalidate.call(this,i)},t.clear=function(i){i===void 0&&(i=!0);for(var s=this._first,a;s;)a=s._next,this.remove(s),s=a;return this._dp&&(this._time=this._tTime=this._pTime=0),i&&(this.labels={}),Vr(this)},t.totalDuration=function(i){var s=0,a=this,o=a._last,l=Jn,c,u,f;if(arguments.length)return a.timeScale((a._repeat<0?a.duration():a.totalDuration())/(a.reversed()?-i:i));if(a._dirty){for(f=a.parent;o;)c=o._prev,o._dirty&&o.totalDuration(),u=o._start,u>l&&a._sort&&o._ts&&!a._lock?(a._lock=1,Ei(a,o,u-o._delay,1)._lock=0):l=u,u<0&&o._ts&&(s-=u,(!f&&!a._dp||f&&f.smoothChildTiming)&&(a._start+=It(u/a._ts),a._time-=u,a._tTime-=u),a.shiftChildren(-u,!1,-1/0),l=0),o._end>s&&o._ts&&(s=o._end),o=c;Vs(a,a===Ft&&a._time>s?a._time:s,1,1),a._dirty=0}return a._tDur},e.updateRoot=function(i){if(Ft._ts&&(g0(Ft,gl(i,Ft)),p0=zn.frame),zn.frame>=gp){gp+=Vn.autoSleep||120;var s=Ft._first;if((!s||!s._ts)&&Vn.autoSleep&&zn._listeners.length<2){for(;s&&!s._ts;)s=s._next;s||zn.sleep()}}},e})(Va);Yn(An.prototype,{_lock:0,_hasPause:0,_forcing:0});var jy=function(e,t,r,i,s,a,o){var l=new Pn(this._pt,e,t,0,1,H0,null,s),c=0,u=0,f,h,d,m,g,p,_,M;for(l.b=r,l.e=i,r+="",i+="",(_=~i.indexOf("random("))&&(i=Ga(i)),a&&(M=[r,i],a(M,e,t),r=M[0],i=M[1]),h=r.match(zc)||[];f=zc.exec(i);)m=f[0],g=i.substring(c,f.index),d?d=(d+1)%5:g.substr(-5)==="rgba("&&(d=1),m!==h[u++]&&(p=parseFloat(h[u-1])||0,l._pt={_next:l._pt,p:g||u===1?g:",",s:p,c:m.charAt(1)==="="?Us(p,m)-p:parseFloat(m)-p,m:d&&d<4?Math.round:0},c=zc.lastIndex);return l.c=c<i.length?i.substring(c,i.length):"",l.fp=o,(u0.test(i)||_)&&(l.e=0),this._pt=l,l},ff=function(e,t,r,i,s,a,o,l,c,u){Gt(i)&&(i=i(s||0,e,a));var f=e[t],h=r!=="get"?r:Gt(f)?c?e[t.indexOf("set")||!Gt(e["get"+t.substr(3)])?t:"get"+t.substr(3)](c):e[t]():f,d=Gt(f)?c?Qy:z0:pf,m;if(on(i)&&(~i.indexOf("random(")&&(i=Ga(i)),i.charAt(1)==="="&&(m=Us(h,i)+(pn(h)||0),(m||m===0)&&(i=m))),!u||h!==i||Rh)return!isNaN(h*i)&&i!==""?(m=new Pn(this._pt,e,t,+h||0,i-(h||0),typeof f=="boolean"?tT:G0,0,d),c&&(m.fp=c),o&&m.modifier(o,this,e),this._pt=m):(!f&&!(t in e)&&of(t,i),jy.call(this,e,t,h,i,d,l||Vn.stringFilter,c))},Ky=function(e,t,r,i,s){if(Gt(e)&&(e=Ia(e,s,t,r,i)),!Ui(e)||e.style&&e.nodeType||gn(e)||l0(e))return on(e)?Ia(e,s,t,r,i):e;var a={},o;for(o in e)a[o]=Ia(e[o],s,t,r,i);return a},O0=function(e,t,r,i,s,a){var o,l,c,u;if(Bn[e]&&(o=new Bn[e]).init(s,o.rawVars?t[e]:Ky(t[e],i,s,a,r),r,i,a)!==!1&&(r._pt=l=new Pn(r._pt,s,e,0,1,o.render,o,0,o.priority),r!==Cs))for(c=r._ptLookup[r._targets.indexOf(s)],u=o._props.length;u--;)c[o._props[u]]=l;return o},hr,Rh,df=function n(e,t,r){var i=e.vars,s=i.ease,a=i.startAt,o=i.immediateRender,l=i.lazy,c=i.onUpdate,u=i.runBackwards,f=i.yoyoEase,h=i.keyframes,d=i.autoRevert,m=e._dur,g=e._startAt,p=e._targets,_=e.parent,M=_&&_.data==="nested"?_.vars.targets:p,y=e._overwrite==="auto"&&!nf,v=e.timeline,S=i.easeReverse||f,b,E,x,w,R,L,A,U,P,I,F,O,q;if(v&&(!h||!s)&&(s="none"),e._ease=Wr(s,Ba.ease),e._rEase=S&&(Wr(S)||e._ease),e._from=!v&&!!i.runBackwards,e._from&&(e.ratio=1),!v||h&&!i.stagger){if(U=p[0]?Hr(p[0]).harness:0,O=U&&i[U.prop],b=ml(i,lf),g&&(g._zTime<0&&g.progress(1),t<0&&u&&o&&!d?g.render(-1,!0):g.revert(u&&m?Qo:by),g._lazy=0),a){if(xr(e._startAt=Xt.set(p,Yn({data:"isStart",overwrite:!1,parent:_,immediateRender:!0,lazy:!g&&Rn(l),startAt:null,delay:0,onUpdate:c&&function(){return Gn(e,"onUpdate")},stagger:0},a))),e._startAt._dp=0,e._startAt._sat=e,t<0&&(un||!o&&!d)&&e._startAt.revert(Qo),o&&m&&t<=0&&r<=0){t&&(e._zTime=t);return}}else if(u&&m&&!g){if(t&&(o=!1),x=Yn({overwrite:!1,data:"isFromStart",lazy:o&&!g&&Rn(l),immediateRender:o,stagger:0,parent:_},b),O&&(x[U.prop]=O),xr(e._startAt=Xt.set(p,x)),e._startAt._dp=0,e._startAt._sat=e,t<0&&(un?e._startAt.revert(Qo):e._startAt.render(-1,!0)),e._zTime=t,!o)n(e._startAt,Et,Et);else if(!t)return}for(e._pt=e._ptCache=0,l=m&&Rn(l)||l&&!m,E=0;E<p.length;E++){if(R=p[E],A=R._gsap||uf(p)[E]._gsap,e._ptLookup[E]=I={},bh[A.id]&&mr.length&&pl(),F=M===p?E:M.indexOf(R),U&&(P=new U).init(R,O||b,e,F,M)!==!1&&(e._pt=w=new Pn(e._pt,R,P.name,0,1,P.render,P,0,P.priority),P._props.forEach(function(z){I[z]=w}),P.priority&&(L=1)),!U||O)for(x in b)Bn[x]&&(P=O0(x,b,e,F,R,M))?P.priority&&(L=1):I[x]=w=ff.call(e,R,x,"get",b[x],F,M,0,i.stringFilter);e._op&&e._op[E]&&e.kill(R,e._op[E]),y&&e._pt&&(hr=e,Ft.killTweensOf(R,I,e.globalTime(t)),q=!e.parent,hr=0),e._pt&&l&&(bh[A.id]=1)}L&&V0(e),e._onInit&&e._onInit(e)}e._onUpdate=c,e._initted=(!e._op||e._pt)&&!q,h&&t<=0&&v.render(Jn,!0,!0)},Zy=function(e,t,r,i,s,a,o,l){var c=(e._pt&&e._ptCache||(e._ptCache={}))[t],u,f,h,d;if(!c)for(c=e._ptCache[t]=[],h=e._ptLookup,d=e._targets.length;d--;){if(u=h[d][t],u&&u.d&&u.d._pt)for(u=u.d._pt;u&&u.p!==t&&u.fp!==t;)u=u._next;if(!u)return Rh=1,e.vars[t]="+=0",df(e,o),Rh=0,l?ka(t+" not eligible for reset. Try splitting into individual properties"):1;c.push(u)}for(d=c.length;d--;)f=c[d],u=f._pt||f,u.s=(i||i===0)&&!s?i:u.s+(i||0)+a*u.c,u.c=r-u.s,f.e&&(f.e=Vt(r)+pn(f.e)),f.b&&(f.b=u.s+pn(f.b))},$y=function(e,t){var r=e[0]?Hr(e[0]).harness:0,i=r&&r.aliases,s,a,o,l;if(!i)return t;s=Gs({},t);for(a in i)if(a in s)for(l=i[a].split(","),o=l.length;o--;)s[l[o]]=s[a];return s},Jy=function(e,t,r,i){var s=t.ease||i||"power1.inOut",a,o;if(gn(t))o=r[e]||(r[e]=[]),t.forEach(function(l,c){return o.push({t:c/(t.length-1)*100,v:l,e:s})});else for(a in t)o=r[a]||(r[a]=[]),a==="ease"||o.push({t:parseFloat(e),v:t[a],e:s})},Ia=function(e,t,r,i,s){return Gt(e)?e.call(t,r,i,s):on(e)&&~e.indexOf("random(")?Ga(e):e},B0=cf+"repeat,repeatDelay,yoyo,repeatRefresh,yoyoEase,easeReverse,autoRevert",k0={};Cn(B0+",id,stagger,delay,duration,paused,scrollTrigger",function(n){return k0[n]=1});var Xt=(function(n){a0(e,n);function e(r,i,s,a){var o;typeof i=="number"&&(s.duration=i,i=s,s=null),o=n.call(this,a?i:Ua(i))||this;var l=o.vars,c=l.duration,u=l.delay,f=l.immediateRender,h=l.stagger,d=l.overwrite,m=l.keyframes,g=l.defaults,p=l.scrollTrigger,_=i.parent||Ft,M=(gn(r)||l0(r)?ji(r[0]):"length"in i)?[r]:Qn(r),y,v,S,b,E,x,w,R;if(o._targets=M.length?uf(M):ka("GSAP target "+r+" not found. https://gsap.com",!Vn.nullTargetWarn)||[],o._ptLookup=[],o._overwrite=d,m||h||Bo(c)||Bo(u)){i=o.vars;var L=i.easeReverse||i.yoyoEase;if(y=o.timeline=new An({data:"nested",defaults:g||{},targets:_&&_.data==="nested"?_.vars.targets:M}),y.kill(),y.parent=y._dp=zi(o),y._start=0,h||Bo(c)||Bo(u)){if(b=M.length,w=h&&E0(h),Ui(h))for(E in h)~B0.indexOf(E)&&(R||(R={}),R[E]=h[E]);for(v=0;v<b;v++)S=ml(i,k0),S.stagger=0,L&&(S.easeReverse=L),R&&Gs(S,R),x=M[v],S.duration=+Ia(c,zi(o),v,x,M),S.delay=(+Ia(u,zi(o),v,x,M)||0)-o._delay,!h&&b===1&&S.delay&&(o._delay=u=S.delay,o._start+=u,S.delay=0),y.to(x,S,w?w(v,x,M):0),y._ease=ht.none;y.duration()?c=u=0:o.timeline=0}else if(m){Ua(Yn(y.vars.defaults,{ease:"none"})),y._ease=Wr(m.ease||i.ease||"none");var A=0,U,P,I;if(gn(m))m.forEach(function(F){return y.to(M,F,">")}),y.duration();else{S={};for(E in m)E==="ease"||E==="easeEach"||Jy(E,m[E],S,m.easeEach);for(E in S)for(U=S[E].sort(function(F,O){return F.t-O.t}),A=0,v=0;v<U.length;v++)P=U[v],I={ease:P.e,duration:(P.t-(v?U[v-1].t:0))/100*c},I[E]=P.v,y.to(M,I,A),A+=I.duration;y.duration()<c&&y.to({},{duration:c-y.duration()})}}c||o.duration(c=y.duration())}else o.timeline=0;return d===!0&&!nf&&(hr=zi(o),Ft.killTweensOf(M),hr=0),Ei(_,zi(o),s),i.reversed&&o.reverse(),i.paused&&o.paused(!0),(f||!c&&!m&&o._start===It(_._time)&&Rn(f)&&Ry(zi(o))&&_.data!=="nested")&&(o._tTime=-Et,o.render(Math.max(0,-u)||0)),p&&S0(zi(o),p),o}var t=e.prototype;return t.render=function(i,s,a){var o=this._time,l=this._tDur,c=this._dur,u=i<0,f=i>l-Et&&!u?l:i<Et?0:i,h,d,m,g,p,_,M,y;if(!c)Py(this,i,s,a);else if(f!==this._tTime||!i||a||!this._initted&&this._tTime||this._startAt&&this._zTime<0!==u||this._lazy){if(h=f,y=this.timeline,this._repeat){if(g=c+this._rDelay,this._repeat<-1&&u)return this.totalTime(g*100+i,s,a);if(h=It(f%g),f===l?(m=this._repeat,h=c):(p=It(f/g),m=~~p,m&&m===p?(h=c,m--):h>c&&(h=c)),_=this._yoyo&&m&1,_&&(h=c-h),p=Hs(this._tTime,g),h===o&&!a&&this._initted&&m===p)return this._tTime=f,this;m!==p&&this.vars.repeatRefresh&&!_&&!this._lock&&h!==g&&this._initted&&(this._lock=a=1,this.render(It(g*m),!0).invalidate()._lock=0)}if(!this._initted){if(b0(this,u?i:h,a,s,f))return this._tTime=0,this;if(o!==this._time&&!(a&&this.vars.repeatRefresh&&m!==p))return this;if(c!==this._dur)return this.render(i,s,a)}if(this._rEase){var v=h<o;if(v!==this._inv){var S=v?o:c-o;this._inv=v,this._from&&(this.ratio=1-this.ratio),this._invRatio=this.ratio,this._invTime=o,this._invRecip=S?(v?-1:1)/S:0,this._invScale=v?-this.ratio:1-this.ratio,this._invEase=v?this._rEase:this._ease}this.ratio=M=this._invRatio+this._invScale*this._invEase((h-this._invTime)*this._invRecip)}else this.ratio=M=this._ease(h/c);if(this._from&&(this.ratio=M=1-M),this._tTime=f,this._time=h,!this._act&&this._ts&&(this._act=1,this._lazy=0),!o&&f&&!s&&!p&&(Gn(this,"onStart"),this._tTime!==f))return this;for(d=this._pt;d;)d.r(M,d.d),d=d._next;y&&y.render(i<0?i:y._dur*y._ease(h/this._dur),s,a)||this._startAt&&(this._zTime=i),this._onUpdate&&!s&&(u&&yh(this,i,s,a),Gn(this,"onUpdate")),this._repeat&&m!==p&&this.vars.onRepeat&&!s&&this.parent&&Gn(this,"onRepeat"),(f===this._tDur||!f)&&this._tTime===f&&(u&&!this._onUpdate&&yh(this,i,!0,!0),(i||!c)&&(f===this._tDur&&this._ts>0||!f&&this._ts<0)&&xr(this,1),!s&&!(u&&!o)&&(f||o||_)&&(Gn(this,f===l?"onComplete":"onReverseComplete",!0),this._prom&&!(f<l&&this.timeScale()>0)&&this._prom()))}return this},t.targets=function(){return this._targets},t.invalidate=function(i){return(!i||!this.vars.runBackwards)&&(this._startAt=0),this._pt=this._op=this._onUpdate=this._lazy=this.ratio=0,this._ptLookup=[],this.timeline&&this.timeline.invalidate(i),n.prototype.invalidate.call(this,i)},t.resetTo=function(i,s,a,o,l){Ha||zn.wake(),this._ts||this.play();var c=Math.min(this._dur,(this._dp._time-this._start)*this._ts),u;return this._initted||df(this,c),u=this._ease(c/this._dur),Zy(this,i,s,a,o,u,c,l)?this.resetTo(i,s,a,o,1):(Il(this,0),this.parent||x0(this._dp,this,"_first","_last",this._dp._sort?"_start":0),this.render(0))},t.kill=function(i,s){if(s===void 0&&(s="all"),!i&&(!s||s==="all"))return this._lazy=this._pt=0,this.parent?Aa(this):this.scrollTrigger&&this.scrollTrigger.kill(!!un),this;if(this.timeline){var a=this.timeline.totalDuration();return this.timeline.killTweensOf(i,s,hr&&hr.vars.overwrite!==!0)._first||Aa(this),this.parent&&a!==this.timeline.totalDuration()&&Vs(this,this._dur*this.timeline._tDur/a,0,1),this}var o=this._targets,l=i?Qn(i):o,c=this._ptLookup,u=this._pt,f,h,d,m,g,p,_;if((!s||s==="all")&&wy(o,l))return s==="all"&&(this._pt=0),Aa(this);for(f=this._op=this._op||[],s!=="all"&&(on(s)&&(g={},Cn(s,function(M){return g[M]=1}),s=g),s=$y(o,s)),_=o.length;_--;)if(~l.indexOf(o[_])){h=c[_],s==="all"?(f[_]=s,m=h,d={}):(d=f[_]=f[_]||{},m=s);for(g in m)p=h&&h[g],p&&((!("kill"in p.d)||p.d.kill(g)===!0)&&Ul(this,p,"_pt"),delete h[g]),d!=="all"&&(d[g]=1)}return this._initted&&!this._pt&&u&&Aa(this),this},e.to=function(i,s){return new e(i,s,arguments[2])},e.from=function(i,s){return La(1,arguments)},e.delayedCall=function(i,s,a,o){return new e(s,0,{immediateRender:!1,lazy:!1,overwrite:!1,delay:i,onComplete:s,onReverseComplete:s,onCompleteParams:a,onReverseCompleteParams:a,callbackScope:o})},e.fromTo=function(i,s,a){return La(2,arguments)},e.set=function(i,s){return s.duration=0,s.repeatDelay||(s.repeat=0),new e(i,s)},e.killTweensOf=function(i,s,a){return Ft.killTweensOf(i,s,a)},e})(Va);Yn(Xt.prototype,{_targets:[],_lazy:0,_startAt:0,_op:0,_onInit:0});Cn("staggerTo,staggerFrom,staggerFromTo",function(n){Xt[n]=function(){var e=new An,t=Eh.call(arguments,0);return t.splice(n==="staggerFromTo"?5:4,0,0),e[n].apply(e,t)}});var pf=function(e,t,r){return e[t]=r},z0=function(e,t,r){return e[t](r)},Qy=function(e,t,r,i){return e[t](i.fp,r)},eT=function(e,t,r){return e.setAttribute(t,r)},mf=function(e,t){return Gt(e[t])?z0:rf(e[t])&&e.setAttribute?eT:pf},G0=function(e,t){return t.set(t.t,t.p,Math.round((t.s+t.c*e)*1e6)/1e6,t)},tT=function(e,t){return t.set(t.t,t.p,!!(t.s+t.c*e),t)},H0=function(e,t){var r=t._pt,i="";if(!e&&t.b)i=t.b;else if(e===1&&t.e)i=t.e;else{for(;r;)i=r.p+(r.m?r.m(r.s+r.c*e):Math.round((r.s+r.c*e)*1e4)/1e4)+i,r=r._next;i+=t.c}t.set(t.t,t.p,i,t)},gf=function(e,t){for(var r=t._pt;r;)r.r(e,r.d),r=r._next},nT=function(e,t,r,i){for(var s=this._pt,a;s;)a=s._next,s.p===i&&s.modifier(e,t,r),s=a},iT=function(e){for(var t=this._pt,r,i;t;)i=t._next,t.p===e&&!t.op||t.op===e?Ul(this,t,"_pt"):t.dep||(r=1),t=i;return!r},rT=function(e,t,r,i){i.mSet(e,t,i.m.call(i.tween,r,i.mt),i)},V0=function(e){for(var t=e._pt,r,i,s,a;t;){for(r=t._next,i=s;i&&i.pr>t.pr;)i=i._next;(t._prev=i?i._prev:a)?t._prev._next=t:s=t,(t._next=i)?i._prev=t:a=t,t=r}e._pt=s},Pn=(function(){function n(t,r,i,s,a,o,l,c,u){this.t=r,this.s=s,this.c=a,this.p=i,this.r=o||G0,this.d=l||this,this.set=c||pf,this.pr=u||0,this._next=t,t&&(t._prev=this)}var e=n.prototype;return e.modifier=function(r,i,s){this.mSet=this.mSet||this.set,this.set=rT,this.m=r,this.mt=s,this.tween=i},n})();Cn(cf+"parent,duration,ease,delay,overwrite,runBackwards,startAt,yoyo,immediateRender,repeat,repeatDelay,data,paused,reversed,lazy,callbackScope,stringFilter,id,yoyoEase,stagger,inherit,repeatRefresh,keyframes,autoRevert,scrollTrigger,easeReverse",function(n){return lf[n]=1});Xn.TweenMax=Xn.TweenLite=Xt;Xn.TimelineLite=Xn.TimelineMax=An;Ft=new An({sortChildren:!1,defaults:Ba,autoRemoveChildren:!0,id:"root",smoothChildTiming:!0});Vn.stringFilter=I0;var Xr=[],tl={},sT=[],bp=0,aT=0,Xc=function(e){return(tl[e]||sT).map(function(t){return t()})},Ch=function(){var e=Date.now(),t=[];e-bp>2&&(Xc("matchMediaInit"),Xr.forEach(function(r){var i=r.queries,s=r.conditions,a,o,l,c;for(o in i)a=Si.matchMedia(i[o]).matches,a&&(l=1),a!==s[o]&&(s[o]=a,c=1);c&&(r.revert(),l&&t.push(r))}),Xc("matchMediaRevert"),t.forEach(function(r){return r.onMatch(r,function(i){return r.add(null,i)})}),bp=e,Xc("matchMedia"))},W0=(function(){function n(t,r){this.selector=r&&wh(r),this.data=[],this._r=[],this.isReverted=!1,this.id=aT++,t&&this.add(t)}var e=n.prototype;return e.add=function(r,i,s){Gt(r)&&(s=i,i=r,r=Gt);var a=this,o=function(){var c=Ut,u=a.selector,f;return c&&c!==a&&c.data.push(a),s&&(a.selector=wh(s)),Ut=a,f=i.apply(a,arguments),Gt(f)&&a._r.push(f),Ut=c,a.selector=u,a.isReverted=!1,f};return a.last=o,r===Gt?o(a,function(l){return a.add(null,l)}):r?a[r]=o:o},e.ignore=function(r){var i=Ut;Ut=null,r(this),Ut=i},e.getTweens=function(){var r=[];return this.data.forEach(function(i){return i instanceof n?r.push.apply(r,i.getTweens()):i instanceof Xt&&!(i.parent&&i.parent.data==="nested")&&r.push(i)}),r},e.clear=function(){this._r.length=this.data.length=0},e.kill=function(r,i){var s=this;if(r?(function(){for(var o=s.getTweens(),l=s.data.length,c;l--;)c=s.data[l],c.data==="isFlip"&&(c.revert(),c.getChildren(!0,!0,!1).forEach(function(u){return o.splice(o.indexOf(u),1)}));for(o.map(function(u){return{g:u._dur||u._delay||u._sat&&!u._sat.vars.immediateRender?u.globalTime(0):-1/0,t:u}}).sort(function(u,f){return f.g-u.g||-1/0}).forEach(function(u){return u.t.revert(r)}),l=s.data.length;l--;)c=s.data[l],c instanceof An?c.data!=="nested"&&(c.scrollTrigger&&c.scrollTrigger.revert(),c.kill()):!(c instanceof Xt)&&c.revert&&c.revert(r);s._r.forEach(function(u){return u(r,s)}),s.isReverted=!0})():this.data.forEach(function(o){return o.kill&&o.kill()}),this.clear(),i)for(var a=Xr.length;a--;)Xr[a].id===this.id&&Xr.splice(a,1)},e.revert=function(r){this.kill(r||{})},n})(),oT=(function(){function n(t){this.contexts=[],this.scope=t,Ut&&Ut.data.push(this)}var e=n.prototype;return e.add=function(r,i,s){Ui(r)||(r={matches:r});var a=new W0(0,s||this.scope),o=a.conditions={},l,c,u;Ut&&!a.selector&&(a.selector=Ut.selector),this.contexts.push(a),i=a.add("onMatch",i),a.queries=r;for(c in r)c==="all"?u=1:(l=Si.matchMedia(r[c]),l&&(Xr.indexOf(a)<0&&Xr.push(a),(o[c]=l.matches)&&(u=1),l.addListener?l.addListener(Ch):l.addEventListener("change",Ch)));return u&&i(a,function(f){return a.add(null,f)}),this},e.revert=function(r){this.kill(r||{})},e.kill=function(r){this.contexts.forEach(function(i){return i.kill(r,!0)})},n})(),_l={registerPlugin:function(){for(var e=arguments.length,t=new Array(e),r=0;r<e;r++)t[r]=arguments[r];t.forEach(function(i){return D0(i)})},timeline:function(e){return new An(e)},getTweensOf:function(e,t){return Ft.getTweensOf(e,t)},getProperty:function(e,t,r,i){on(e)&&(e=Qn(e)[0]);var s=Hr(e||{}).get,a=r?v0:_0;return r==="native"&&(r=""),e&&(t?a((Bn[t]&&Bn[t].get||s)(e,t,r,i)):function(o,l,c){return a((Bn[o]&&Bn[o].get||s)(e,o,l,c))})},quickSetter:function(e,t,r){if(e=Qn(e),e.length>1){var i=e.map(function(u){return Un.quickSetter(u,t,r)}),s=i.length;return function(u){for(var f=s;f--;)i[f](u)}}e=e[0]||{};var a=Bn[t],o=Hr(e),l=o.harness&&(o.harness.aliases||{})[t]||t,c=a?function(u){var f=new a;Cs._pt=0,f.init(e,r?u+r:u,Cs,0,[e]),f.render(1,f),Cs._pt&&gf(1,Cs)}:o.set(e,l);return a?c:function(u){return c(e,l,r?u+r:u,o,1)}},quickTo:function(e,t,r){var i,s=Un.to(e,Yn((i={},i[t]="+=0.1",i.paused=!0,i.stagger=0,i),r||{})),a=function(l,c,u){return s.resetTo(t,l,c,u)};return a.tween=s,a},isTweening:function(e){return Ft.getTweensOf(e,!0).length>0},defaults:function(e){return e&&e.ease&&(e.ease=Wr(e.ease,Ba.ease)),_p(Ba,e||{})},config:function(e){return _p(Vn,e||{})},registerEffect:function(e){var t=e.name,r=e.effect,i=e.plugins,s=e.defaults,a=e.extendTimeline;(i||"").split(",").forEach(function(o){return o&&!Bn[o]&&!Xn[o]&&ka(t+" effect requires "+o+" plugin.")}),Gc[t]=function(o,l,c){return r(Qn(o),Yn(l||{},s),c)},a&&(An.prototype[t]=function(o,l,c){return this.add(Gc[t](o,Ui(l)?l:(c=l)&&{},this),c)})},registerEase:function(e,t){ht[e]=Wr(t)},parseEase:function(e,t){return arguments.length?Wr(e,t):ht},getById:function(e){return Ft.getById(e)},exportRoot:function(e,t){e===void 0&&(e={});var r=new An(e),i,s;for(r.smoothChildTiming=Rn(e.smoothChildTiming),Ft.remove(r),r._dp=0,r._time=r._tTime=Ft._time,i=Ft._first;i;)s=i._next,(t||!(!i._dur&&i instanceof Xt&&i.vars.onComplete===i._targets[0]))&&Ei(r,i,i._start-i._delay),i=s;return Ei(Ft,r,0),r},context:function(e,t){return e?new W0(e,t):Ut},matchMedia:function(e){return new oT(e)},matchMediaRefresh:function(){return Xr.forEach(function(e){var t=e.conditions,r,i;for(i in t)t[i]&&(t[i]=!1,r=1);r&&e.revert()})||Ch()},addEventListener:function(e,t){var r=tl[e]||(tl[e]=[]);~r.indexOf(t)||r.push(t)},removeEventListener:function(e,t){var r=tl[e],i=r&&r.indexOf(t);i>=0&&r.splice(i,1)},utils:{wrap:By,wrapYoyo:ky,distribute:E0,random:A0,snap:w0,normalize:Oy,getUnit:pn,clamp:Ly,splitColor:U0,toArray:Qn,selector:wh,mapRange:C0,pipe:Fy,unitize:Ny,interpolate:zy,shuffle:T0},install:f0,effects:Gc,ticker:zn,updateRoot:An.updateRoot,plugins:Bn,globalTimeline:Ft,core:{PropTween:Pn,globals:d0,Tween:Xt,Timeline:An,Animation:Va,getCache:Hr,_removeLinkedListItem:Ul,reverting:function(){return un},context:function(e){return e&&Ut&&(Ut.data.push(e),e._ctx=Ut),Ut},suppressOverwrites:function(e){return nf=e}}};Cn("to,from,fromTo,delayedCall,set,killTweensOf",function(n){return _l[n]=Xt[n]});zn.add(An.updateRoot);Cs=_l.to({},{duration:0});var lT=function(e,t){for(var r=e._pt;r&&r.p!==t&&r.op!==t&&r.fp!==t;)r=r._next;return r},cT=function(e,t){var r=e._targets,i,s,a;for(i in t)for(s=r.length;s--;)a=e._ptLookup[s][i],a&&(a=a.d)&&(a._pt&&(a=lT(a,i)),a&&a.modifier&&a.modifier(t[i],e,r[s],i))},Yc=function(e,t){return{name:e,headless:1,rawVars:1,init:function(i,s,a){a._onInit=function(o){var l,c;if(on(s)&&(l={},Cn(s,function(u){return l[u]=1}),s=l),t){l={};for(c in s)l[c]=t(s[c]);s=l}cT(o,s)}}}},Un=_l.registerPlugin({name:"attr",init:function(e,t,r,i,s){var a,o,l;this.tween=r;for(a in t)l=e.getAttribute(a)||"",o=this.add(e,"setAttribute",(l||0)+"",t[a],i,s,0,0,a),o.op=a,o.b=l,this._props.push(a)},render:function(e,t){for(var r=t._pt;r;)un?r.set(r.t,r.p,r.b,r):r.r(e,r.d),r=r._next}},{name:"endArray",headless:1,init:function(e,t){for(var r=t.length;r--;)this.add(e,r,e[r]||0,t[r],0,0,0,0,0,1)}},Yc("roundProps",Ah),Yc("modifiers"),Yc("snap",w0))||_l;Xt.version=An.version=Un.version="3.15.0";h0=1;sf()&&Ws();ht.Power0;ht.Power1;ht.Power2;ht.Power3;ht.Power4;ht.Linear;ht.Quad;ht.Cubic;ht.Quart;ht.Quint;ht.Strong;ht.Elastic;ht.Back;ht.SteppedEase;ht.Bounce;ht.Sine;ht.Expo;ht.Circ;/*!
 * CSSPlugin 3.15.0
 * https://gsap.com
 *
 * Copyright 2008-2026, GreenSock. All rights reserved.
 * Subject to the terms at https://gsap.com/standard-license
 * @author: Jack Doyle, jack@greensock.com
*/var yp,fr,Ls,_f,kr,Tp,vf,uT=function(){return typeof window<"u"},Ki={},Fr=180/Math.PI,Is=Math.PI/180,Es=Math.atan2,Ep=1e8,xf=/([A-Z])/g,hT=/(left|right|width|margin|padding|x)/i,fT=/[\s,\(]\S/,Ri={autoAlpha:"opacity,visibility",scale:"scaleX,scaleY",alpha:"opacity"},Ph=function(e,t){return t.set(t.t,t.p,Math.round((t.s+t.c*e)*1e4)/1e4+t.u,t)},dT=function(e,t){return t.set(t.t,t.p,e===1?t.e:Math.round((t.s+t.c*e)*1e4)/1e4+t.u,t)},pT=function(e,t){return t.set(t.t,t.p,e?Math.round((t.s+t.c*e)*1e4)/1e4+t.u:t.b,t)},mT=function(e,t){return t.set(t.t,t.p,e===1?t.e:e?Math.round((t.s+t.c*e)*1e4)/1e4+t.u:t.b,t)},gT=function(e,t){var r=t.s+t.c*e;t.set(t.t,t.p,~~(r+(r<0?-.5:.5))+t.u,t)},X0=function(e,t){return t.set(t.t,t.p,e?t.e:t.b,t)},Y0=function(e,t){return t.set(t.t,t.p,e!==1?t.b:t.e,t)},_T=function(e,t,r){return e.style[t]=r},vT=function(e,t,r){return e.style.setProperty(t,r)},xT=function(e,t,r){return e._gsap[t]=r},MT=function(e,t,r){return e._gsap.scaleX=e._gsap.scaleY=r},ST=function(e,t,r,i,s){var a=e._gsap;a.scaleX=a.scaleY=r,a.renderTransform(s,a)},bT=function(e,t,r,i,s){var a=e._gsap;a[t]=r,a.renderTransform(s,a)},Nt="transform",Dn=Nt+"Origin",yT=function n(e,t){var r=this,i=this.target,s=i.style,a=i._gsap;if(e in Ki&&s){if(this.tfm=this.tfm||{},e!=="transform")e=Ri[e]||e,~e.indexOf(",")?e.split(",").forEach(function(o){return r.tfm[o]=Gi(i,o)}):this.tfm[e]=a.x?a[e]:Gi(i,e),e===Dn&&(this.tfm.zOrigin=a.zOrigin);else return Ri.transform.split(",").forEach(function(o){return n.call(r,o,t)});if(this.props.indexOf(Nt)>=0)return;a.svg&&(this.svgo=i.getAttribute("data-svg-origin"),this.props.push(Dn,t,"")),e=Nt}(s||t)&&this.props.push(e,t,s[e])},q0=function(e){e.translate&&(e.removeProperty("translate"),e.removeProperty("scale"),e.removeProperty("rotate"))},TT=function(){var e=this.props,t=this.target,r=t.style,i=t._gsap,s,a;for(s=0;s<e.length;s+=3)e[s+1]?e[s+1]===2?t[e[s]](e[s+2]):t[e[s]]=e[s+2]:e[s+2]?r[e[s]]=e[s+2]:r.removeProperty(e[s].substr(0,2)==="--"?e[s]:e[s].replace(xf,"-$1").toLowerCase());if(this.tfm){for(a in this.tfm)i[a]=this.tfm[a];i.svg&&(i.renderTransform(),t.setAttribute("data-svg-origin",this.svgo||"")),s=vf(),(!s||!s.isStart)&&!r[Nt]&&(q0(r),i.zOrigin&&r[Dn]&&(r[Dn]+=" "+i.zOrigin+"px",i.zOrigin=0,i.renderTransform()),i.uncache=1)}},j0=function(e,t){var r={target:e,props:[],revert:TT,save:yT};return e._gsap||Un.core.getCache(e),t&&e.style&&e.nodeType&&t.split(",").forEach(function(i){return r.save(i)}),r},K0,Dh=function(e,t){var r=fr.createElementNS?fr.createElementNS((t||"http://www.w3.org/1999/xhtml").replace(/^https/,"http"),e):fr.createElement(e);return r&&r.style?r:fr.createElement(e)},Hn=function n(e,t,r){var i=getComputedStyle(e);return i[t]||i.getPropertyValue(t.replace(xf,"-$1").toLowerCase())||i.getPropertyValue(t)||!r&&n(e,Xs(t)||t,1)||""},wp="O,Moz,ms,Ms,Webkit".split(","),Xs=function(e,t,r){var i=t||kr,s=i.style,a=5;if(e in s&&!r)return e;for(e=e.charAt(0).toUpperCase()+e.substr(1);a--&&!(wp[a]+e in s););return a<0?null:(a===3?"ms":a>=0?wp[a]:"")+e},Uh=function(){uT()&&window.document&&(yp=window,fr=yp.document,Ls=fr.documentElement,kr=Dh("div")||{style:{}},Dh("div"),Nt=Xs(Nt),Dn=Nt+"Origin",kr.style.cssText="border-width:0;line-height:0;position:absolute;padding:0",K0=!!Xs("perspective"),vf=Un.core.reverting,_f=1)},Ap=function(e){var t=e.ownerSVGElement,r=Dh("svg",t&&t.getAttribute("xmlns")||"http://www.w3.org/2000/svg"),i=e.cloneNode(!0),s;i.style.display="block",r.appendChild(i),Ls.appendChild(r);try{s=i.getBBox()}catch{}return r.removeChild(i),Ls.removeChild(r),s},Rp=function(e,t){for(var r=t.length;r--;)if(e.hasAttribute(t[r]))return e.getAttribute(t[r])},Z0=function(e){var t,r;try{t=e.getBBox()}catch{t=Ap(e),r=1}return t&&(t.width||t.height)||r||(t=Ap(e)),t&&!t.width&&!t.x&&!t.y?{x:+Rp(e,["x","cx","x1"])||0,y:+Rp(e,["y","cy","y1"])||0,width:0,height:0}:t},$0=function(e){return!!(e.getCTM&&(!e.parentNode||e.ownerSVGElement)&&Z0(e))},Mr=function(e,t){if(t){var r=e.style,i;t in Ki&&t!==Dn&&(t=Nt),r.removeProperty?(i=t.substr(0,2),(i==="ms"||t.substr(0,6)==="webkit")&&(t="-"+t),r.removeProperty(i==="--"?t:t.replace(xf,"-$1").toLowerCase())):r.removeAttribute(t)}},dr=function(e,t,r,i,s,a){var o=new Pn(e._pt,t,r,0,1,a?Y0:X0);return e._pt=o,o.b=i,o.e=s,e._props.push(r),o},Cp={deg:1,rad:1,turn:1},ET={grid:1,flex:1},Sr=function n(e,t,r,i){var s=parseFloat(r)||0,a=(r+"").trim().substr((s+"").length)||"px",o=kr.style,l=hT.test(t),c=e.tagName.toLowerCase()==="svg",u=(c?"client":"offset")+(l?"Width":"Height"),f=100,h=i==="px",d=i==="%",m,g,p,_;if(i===a||!s||Cp[i]||Cp[a])return s;if(a!=="px"&&!h&&(s=n(e,t,r,"px")),_=e.getCTM&&$0(e),(d||a==="%")&&(Ki[t]||~t.indexOf("adius")))return m=_?e.getBBox()[l?"width":"height"]:e[u],Vt(d?s/m*f:s/100*m);if(o[l?"width":"height"]=f+(h?a:i),g=i!=="rem"&&~t.indexOf("adius")||i==="em"&&e.appendChild&&!c?e:e.parentNode,_&&(g=(e.ownerSVGElement||{}).parentNode),(!g||g===fr||!g.appendChild)&&(g=fr.body),p=g._gsap,p&&d&&p.width&&l&&p.time===zn.time&&!p.uncache)return Vt(s/p.width*f);if(d&&(t==="height"||t==="width")){var M=e.style[t];e.style[t]=f+i,m=e[u],M?e.style[t]=M:Mr(e,t)}else(d||a==="%")&&!ET[Hn(g,"display")]&&(o.position=Hn(e,"position")),g===e&&(o.position="static"),g.appendChild(kr),m=kr[u],g.removeChild(kr),o.position="absolute";return l&&d&&(p=Hr(g),p.time=zn.time,p.width=g[u]),Vt(h?m*s/f:m&&s?f/m*s:0)},Gi=function(e,t,r,i){var s;return _f||Uh(),t in Ri&&t!=="transform"&&(t=Ri[t],~t.indexOf(",")&&(t=t.split(",")[0])),Ki[t]&&t!=="transform"?(s=Xa(e,i),s=t!=="transformOrigin"?s[t]:s.svg?s.origin:xl(Hn(e,Dn))+" "+s.zOrigin+"px"):(s=e.style[t],(!s||s==="auto"||i||~(s+"").indexOf("calc("))&&(s=vl[t]&&vl[t](e,t,r)||Hn(e,t)||m0(e,t)||(t==="opacity"?1:0))),r&&!~(s+"").trim().indexOf(" ")?Sr(e,t,s,r)+r:s},wT=function(e,t,r,i){if(!r||r==="none"){var s=Xs(t,e,1),a=s&&Hn(e,s,1);a&&a!==r?(t=s,r=a):t==="borderColor"&&(r=Hn(e,"borderTopColor"))}var o=new Pn(this._pt,e.style,t,0,1,H0),l=0,c=0,u,f,h,d,m,g,p,_,M,y,v,S;if(o.b=r,o.e=i,r+="",i+="",i.substring(0,6)==="var(--"&&(i=Hn(e,i.substring(4,i.indexOf(")")))),i==="auto"&&(g=e.style[t],e.style[t]=i,i=Hn(e,t)||i,g?e.style[t]=g:Mr(e,t)),u=[r,i],I0(u),r=u[0],i=u[1],h=r.match(Rs)||[],S=i.match(Rs)||[],S.length){for(;f=Rs.exec(i);)p=f[0],M=i.substring(l,f.index),m?m=(m+1)%5:(M.substr(-5)==="rgba("||M.substr(-5)==="hsla(")&&(m=1),p!==(g=h[c++]||"")&&(d=parseFloat(g)||0,v=g.substr((d+"").length),p.charAt(1)==="="&&(p=Us(d,p)+v),_=parseFloat(p),y=p.substr((_+"").length),l=Rs.lastIndex-y.length,y||(y=y||Vn.units[t]||v,l===i.length&&(i+=y,o.e+=y)),v!==y&&(d=Sr(e,t,g,y)||0),o._pt={_next:o._pt,p:M||c===1?M:",",s:d,c:_-d,m:m&&m<4||t==="zIndex"?Math.round:0});o.c=l<i.length?i.substring(l,i.length):""}else o.r=t==="display"&&i==="none"?Y0:X0;return u0.test(i)&&(o.e=0),this._pt=o,o},Pp={top:"0%",bottom:"100%",left:"0%",right:"100%",center:"50%"},AT=function(e){var t=e.split(" "),r=t[0],i=t[1]||"50%";return(r==="top"||r==="bottom"||i==="left"||i==="right")&&(e=r,r=i,i=e),t[0]=Pp[r]||r,t[1]=Pp[i]||i,t.join(" ")},RT=function(e,t){if(t.tween&&t.tween._time===t.tween._dur){var r=t.t,i=r.style,s=t.u,a=r._gsap,o,l,c;if(s==="all"||s===!0)i.cssText="",l=1;else for(s=s.split(","),c=s.length;--c>-1;)o=s[c],Ki[o]&&(l=1,o=o==="transformOrigin"?Dn:Nt),Mr(r,o);l&&(Mr(r,Nt),a&&(a.svg&&r.removeAttribute("transform"),i.scale=i.rotate=i.translate="none",Xa(r,1),a.uncache=1,q0(i)))}},vl={clearProps:function(e,t,r,i,s){if(s.data!=="isFromStart"){var a=e._pt=new Pn(e._pt,t,r,0,0,RT);return a.u=i,a.pr=-10,a.tween=s,e._props.push(r),1}}},Wa=[1,0,0,1,0,0],J0={},Q0=function(e){return e==="matrix(1, 0, 0, 1, 0, 0)"||e==="none"||!e},Dp=function(e){var t=Hn(e,Nt);return Q0(t)?Wa:t.substr(7).match(c0).map(Vt)},Mf=function(e,t){var r=e._gsap||Hr(e),i=e.style,s=Dp(e),a,o,l,c;return r.svg&&e.getAttribute("transform")?(l=e.transform.baseVal.consolidate().matrix,s=[l.a,l.b,l.c,l.d,l.e,l.f],s.join(",")==="1,0,0,1,0,0"?Wa:s):(s===Wa&&!e.offsetParent&&e!==Ls&&!r.svg&&(l=i.display,i.display="block",a=e.parentNode,(!a||!e.offsetParent&&!e.getBoundingClientRect().width)&&(c=1,o=e.nextElementSibling,Ls.appendChild(e)),s=Dp(e),l?i.display=l:Mr(e,"display"),c&&(o?a.insertBefore(e,o):a?a.appendChild(e):Ls.removeChild(e))),t&&s.length>6?[s[0],s[1],s[4],s[5],s[12],s[13]]:s)},Lh=function(e,t,r,i,s,a){var o=e._gsap,l=s||Mf(e,!0),c=o.xOrigin||0,u=o.yOrigin||0,f=o.xOffset||0,h=o.yOffset||0,d=l[0],m=l[1],g=l[2],p=l[3],_=l[4],M=l[5],y=t.split(" "),v=parseFloat(y[0])||0,S=parseFloat(y[1])||0,b,E,x,w;r?l!==Wa&&(E=d*p-m*g)&&(x=v*(p/E)+S*(-g/E)+(g*M-p*_)/E,w=v*(-m/E)+S*(d/E)-(d*M-m*_)/E,v=x,S=w):(b=Z0(e),v=b.x+(~y[0].indexOf("%")?v/100*b.width:v),S=b.y+(~(y[1]||y[0]).indexOf("%")?S/100*b.height:S)),i||i!==!1&&o.smooth?(_=v-c,M=S-u,o.xOffset=f+(_*d+M*g)-_,o.yOffset=h+(_*m+M*p)-M):o.xOffset=o.yOffset=0,o.xOrigin=v,o.yOrigin=S,o.smooth=!!i,o.origin=t,o.originIsAbsolute=!!r,e.style[Dn]="0px 0px",a&&(dr(a,o,"xOrigin",c,v),dr(a,o,"yOrigin",u,S),dr(a,o,"xOffset",f,o.xOffset),dr(a,o,"yOffset",h,o.yOffset)),e.setAttribute("data-svg-origin",v+" "+S)},Xa=function(e,t){var r=e._gsap||new N0(e);if("x"in r&&!t&&!r.uncache)return r;var i=e.style,s=r.scaleX<0,a="px",o="deg",l=getComputedStyle(e),c=Hn(e,Dn)||"0",u,f,h,d,m,g,p,_,M,y,v,S,b,E,x,w,R,L,A,U,P,I,F,O,q,z,k,N,G,K,J,j;return u=f=h=g=p=_=M=y=v=0,d=m=1,r.svg=!!(e.getCTM&&$0(e)),l.translate&&((l.translate!=="none"||l.scale!=="none"||l.rotate!=="none")&&(i[Nt]=(l.translate!=="none"?"translate3d("+(l.translate+" 0 0").split(" ").slice(0,3).join(", ")+") ":"")+(l.rotate!=="none"?"rotate("+l.rotate+") ":"")+(l.scale!=="none"?"scale("+l.scale.split(" ").join(",")+") ":"")+(l[Nt]!=="none"?l[Nt]:"")),i.scale=i.rotate=i.translate="none"),E=Mf(e,r.svg),r.svg&&(r.uncache?(q=e.getBBox(),c=r.xOrigin-q.x+"px "+(r.yOrigin-q.y)+"px",O=""):O=!t&&e.getAttribute("data-svg-origin"),Lh(e,O||c,!!O||r.originIsAbsolute,r.smooth!==!1,E)),S=r.xOrigin||0,b=r.yOrigin||0,E!==Wa&&(L=E[0],A=E[1],U=E[2],P=E[3],u=I=E[4],f=F=E[5],E.length===6?(d=Math.sqrt(L*L+A*A),m=Math.sqrt(P*P+U*U),g=L||A?Es(A,L)*Fr:0,M=U||P?Es(U,P)*Fr+g:0,M&&(m*=Math.abs(Math.cos(M*Is))),r.svg&&(u-=S-(S*L+b*U),f-=b-(S*A+b*P))):(j=E[6],K=E[7],k=E[8],N=E[9],G=E[10],J=E[11],u=E[12],f=E[13],h=E[14],x=Es(j,G),p=x*Fr,x&&(w=Math.cos(-x),R=Math.sin(-x),O=I*w+k*R,q=F*w+N*R,z=j*w+G*R,k=I*-R+k*w,N=F*-R+N*w,G=j*-R+G*w,J=K*-R+J*w,I=O,F=q,j=z),x=Es(-U,G),_=x*Fr,x&&(w=Math.cos(-x),R=Math.sin(-x),O=L*w-k*R,q=A*w-N*R,z=U*w-G*R,J=P*R+J*w,L=O,A=q,U=z),x=Es(A,L),g=x*Fr,x&&(w=Math.cos(x),R=Math.sin(x),O=L*w+A*R,q=I*w+F*R,A=A*w-L*R,F=F*w-I*R,L=O,I=q),p&&Math.abs(p)+Math.abs(g)>359.9&&(p=g=0,_=180-_),d=Vt(Math.sqrt(L*L+A*A+U*U)),m=Vt(Math.sqrt(F*F+j*j)),x=Es(I,F),M=Math.abs(x)>2e-4?x*Fr:0,v=J?1/(J<0?-J:J):0),r.svg&&(O=e.getAttribute("transform"),r.forceCSS=e.setAttribute("transform","")||!Q0(Hn(e,Nt)),O&&e.setAttribute("transform",O))),Math.abs(M)>90&&Math.abs(M)<270&&(s?(d*=-1,M+=g<=0?180:-180,g+=g<=0?180:-180):(m*=-1,M+=M<=0?180:-180)),t=t||r.uncache,r.x=u-((r.xPercent=u&&(!t&&r.xPercent||(Math.round(e.offsetWidth/2)===Math.round(-u)?-50:0)))?e.offsetWidth*r.xPercent/100:0)+a,r.y=f-((r.yPercent=f&&(!t&&r.yPercent||(Math.round(e.offsetHeight/2)===Math.round(-f)?-50:0)))?e.offsetHeight*r.yPercent/100:0)+a,r.z=h+a,r.scaleX=Vt(d),r.scaleY=Vt(m),r.rotation=Vt(g)+o,r.rotationX=Vt(p)+o,r.rotationY=Vt(_)+o,r.skewX=M+o,r.skewY=y+o,r.transformPerspective=v+a,(r.zOrigin=parseFloat(c.split(" ")[2])||!t&&r.zOrigin||0)&&(i[Dn]=xl(c)),r.xOffset=r.yOffset=0,r.force3D=Vn.force3D,r.renderTransform=r.svg?PT:K0?eg:CT,r.uncache=0,r},xl=function(e){return(e=e.split(" "))[0]+" "+e[1]},qc=function(e,t,r){var i=pn(t);return Vt(parseFloat(t)+parseFloat(Sr(e,"x",r+"px",i)))+i},CT=function(e,t){t.z="0px",t.rotationY=t.rotationX="0deg",t.force3D=0,eg(e,t)},Ur="0deg",Sa="0px",Lr=") ",eg=function(e,t){var r=t||this,i=r.xPercent,s=r.yPercent,a=r.x,o=r.y,l=r.z,c=r.rotation,u=r.rotationY,f=r.rotationX,h=r.skewX,d=r.skewY,m=r.scaleX,g=r.scaleY,p=r.transformPerspective,_=r.force3D,M=r.target,y=r.zOrigin,v="",S=_==="auto"&&e&&e!==1||_===!0;if(y&&(f!==Ur||u!==Ur)){var b=parseFloat(u)*Is,E=Math.sin(b),x=Math.cos(b),w;b=parseFloat(f)*Is,w=Math.cos(b),a=qc(M,a,E*w*-y),o=qc(M,o,-Math.sin(b)*-y),l=qc(M,l,x*w*-y+y)}p!==Sa&&(v+="perspective("+p+Lr),(i||s)&&(v+="translate("+i+"%, "+s+"%) "),(S||a!==Sa||o!==Sa||l!==Sa)&&(v+=l!==Sa||S?"translate3d("+a+", "+o+", "+l+") ":"translate("+a+", "+o+Lr),c!==Ur&&(v+="rotate("+c+Lr),u!==Ur&&(v+="rotateY("+u+Lr),f!==Ur&&(v+="rotateX("+f+Lr),(h!==Ur||d!==Ur)&&(v+="skew("+h+", "+d+Lr),(m!==1||g!==1)&&(v+="scale("+m+", "+g+Lr),M.style[Nt]=v||"translate(0, 0)"},PT=function(e,t){var r=t||this,i=r.xPercent,s=r.yPercent,a=r.x,o=r.y,l=r.rotation,c=r.skewX,u=r.skewY,f=r.scaleX,h=r.scaleY,d=r.target,m=r.xOrigin,g=r.yOrigin,p=r.xOffset,_=r.yOffset,M=r.forceCSS,y=parseFloat(a),v=parseFloat(o),S,b,E,x,w;l=parseFloat(l),c=parseFloat(c),u=parseFloat(u),u&&(u=parseFloat(u),c+=u,l+=u),l||c?(l*=Is,c*=Is,S=Math.cos(l)*f,b=Math.sin(l)*f,E=Math.sin(l-c)*-h,x=Math.cos(l-c)*h,c&&(u*=Is,w=Math.tan(c-u),w=Math.sqrt(1+w*w),E*=w,x*=w,u&&(w=Math.tan(u),w=Math.sqrt(1+w*w),S*=w,b*=w)),S=Vt(S),b=Vt(b),E=Vt(E),x=Vt(x)):(S=f,x=h,b=E=0),(y&&!~(a+"").indexOf("px")||v&&!~(o+"").indexOf("px"))&&(y=Sr(d,"x",a,"px"),v=Sr(d,"y",o,"px")),(m||g||p||_)&&(y=Vt(y+m-(m*S+g*E)+p),v=Vt(v+g-(m*b+g*x)+_)),(i||s)&&(w=d.getBBox(),y=Vt(y+i/100*w.width),v=Vt(v+s/100*w.height)),w="matrix("+S+","+b+","+E+","+x+","+y+","+v+")",d.setAttribute("transform",w),M&&(d.style[Nt]=w)},DT=function(e,t,r,i,s){var a=360,o=on(s),l=parseFloat(s)*(o&&~s.indexOf("rad")?Fr:1),c=l-i,u=i+c+"deg",f,h;return o&&(f=s.split("_")[1],f==="short"&&(c%=a,c!==c%(a/2)&&(c+=c<0?a:-a)),f==="cw"&&c<0?c=(c+a*Ep)%a-~~(c/a)*a:f==="ccw"&&c>0&&(c=(c-a*Ep)%a-~~(c/a)*a)),e._pt=h=new Pn(e._pt,t,r,i,c,dT),h.e=u,h.u="deg",e._props.push(r),h},Up=function(e,t){for(var r in t)e[r]=t[r];return e},UT=function(e,t,r){var i=Up({},r._gsap),s="perspective,force3D,transformOrigin,svgOrigin",a=r.style,o,l,c,u,f,h,d,m;i.svg?(c=r.getAttribute("transform"),r.setAttribute("transform",""),a[Nt]=t,o=Xa(r,1),Mr(r,Nt),r.setAttribute("transform",c)):(c=getComputedStyle(r)[Nt],a[Nt]=t,o=Xa(r,1),a[Nt]=c);for(l in Ki)c=i[l],u=o[l],c!==u&&s.indexOf(l)<0&&(d=pn(c),m=pn(u),f=d!==m?Sr(r,l,c,m):parseFloat(c),h=parseFloat(u),e._pt=new Pn(e._pt,o,l,f,h-f,Ph),e._pt.u=m||0,e._props.push(l));Up(o,i)};Cn("padding,margin,Width,Radius",function(n,e){var t="Top",r="Right",i="Bottom",s="Left",a=(e<3?[t,r,i,s]:[t+s,t+r,i+r,i+s]).map(function(o){return e<2?n+o:"border"+o+n});vl[e>1?"border"+n:n]=function(o,l,c,u,f){var h,d;if(arguments.length<4)return h=a.map(function(m){return Gi(o,m,c)}),d=h.join(" "),d.split(h[0]).length===5?h[0]:d;h=(u+"").split(" "),d={},a.forEach(function(m,g){return d[m]=h[g]=h[g]||h[(g-1)/2|0]}),o.init(l,d,f)}});var tg={name:"css",register:Uh,targetTest:function(e){return e.style&&e.nodeType},init:function(e,t,r,i,s){var a=this._props,o=e.style,l=r.vars.startAt,c,u,f,h,d,m,g,p,_,M,y,v,S,b,E,x,w;_f||Uh(),this.styles=this.styles||j0(e),x=this.styles.props,this.tween=r;for(g in t)if(g!=="autoRound"&&(u=t[g],!(Bn[g]&&O0(g,t,r,i,e,s)))){if(d=typeof u,m=vl[g],d==="function"&&(u=u.call(r,i,e,s),d=typeof u),d==="string"&&~u.indexOf("random(")&&(u=Ga(u)),m)m(this,e,g,u,r)&&(E=1);else if(g.substr(0,2)==="--")c=(getComputedStyle(e).getPropertyValue(g)+"").trim(),u+="",gr.lastIndex=0,gr.test(c)||(p=pn(c),_=pn(u),_?p!==_&&(c=Sr(e,g,c,_)+_):p&&(u+=p)),this.add(o,"setProperty",c,u,i,s,0,0,g),a.push(g),x.push(g,0,o[g]);else if(d!=="undefined"){if(l&&g in l?(c=typeof l[g]=="function"?l[g].call(r,i,e,s):l[g],on(c)&&~c.indexOf("random(")&&(c=Ga(c)),pn(c+"")||c==="auto"||(c+=Vn.units[g]||pn(Gi(e,g))||""),(c+"").charAt(1)==="="&&(c=Gi(e,g))):c=Gi(e,g),h=parseFloat(c),M=d==="string"&&u.charAt(1)==="="&&u.substr(0,2),M&&(u=u.substr(2)),f=parseFloat(u),g in Ri&&(g==="autoAlpha"&&(h===1&&Gi(e,"visibility")==="hidden"&&f&&(h=0),x.push("visibility",0,o.visibility),dr(this,o,"visibility",h?"inherit":"hidden",f?"inherit":"hidden",!f)),g!=="scale"&&g!=="transform"&&(g=Ri[g],~g.indexOf(",")&&(g=g.split(",")[0]))),y=g in Ki,y){if(this.styles.save(g),w=u,d==="string"&&u.substring(0,6)==="var(--"){if(u=Hn(e,u.substring(4,u.indexOf(")"))),u.substring(0,5)==="calc("){var R=e.style.perspective;e.style.perspective=u,u=Hn(e,"perspective"),R?e.style.perspective=R:Mr(e,"perspective")}f=parseFloat(u)}if(v||(S=e._gsap,S.renderTransform&&!t.parseTransform||Xa(e,t.parseTransform),b=t.smoothOrigin!==!1&&S.smooth,v=this._pt=new Pn(this._pt,o,Nt,0,1,S.renderTransform,S,0,-1),v.dep=1),g==="scale")this._pt=new Pn(this._pt,S,"scaleY",S.scaleY,(M?Us(S.scaleY,M+f):f)-S.scaleY||0,Ph),this._pt.u=0,a.push("scaleY",g),g+="X";else if(g==="transformOrigin"){x.push(Dn,0,o[Dn]),u=AT(u),S.svg?Lh(e,u,0,b,0,this):(_=parseFloat(u.split(" ")[2])||0,_!==S.zOrigin&&dr(this,S,"zOrigin",S.zOrigin,_),dr(this,o,g,xl(c),xl(u)));continue}else if(g==="svgOrigin"){Lh(e,u,1,b,0,this);continue}else if(g in J0){DT(this,S,g,h,M?Us(h,M+u):u);continue}else if(g==="smoothOrigin"){dr(this,S,"smooth",S.smooth,u);continue}else if(g==="force3D"){S[g]=u;continue}else if(g==="transform"){UT(this,u,e);continue}}else g in o||(g=Xs(g)||g);if(y||(f||f===0)&&(h||h===0)&&!fT.test(u)&&g in o)p=(c+"").substr((h+"").length),f||(f=0),_=pn(u)||(g in Vn.units?Vn.units[g]:p),p!==_&&(h=Sr(e,g,c,_)),this._pt=new Pn(this._pt,y?S:o,g,h,(M?Us(h,M+f):f)-h,!y&&(_==="px"||g==="zIndex")&&t.autoRound!==!1?gT:Ph),this._pt.u=_||0,y&&w!==u?(this._pt.b=c,this._pt.e=w,this._pt.r=mT):p!==_&&_!=="%"&&(this._pt.b=c,this._pt.r=pT);else if(g in o)wT.call(this,e,g,c,M?M+u:u);else if(g in e)this.add(e,g,c||e[g],M?M+u:u,i,s);else if(g!=="parseTransform"){of(g,u);continue}y||(g in o?x.push(g,0,o[g]):typeof e[g]=="function"?x.push(g,2,e[g]()):x.push(g,1,c||e[g])),a.push(g)}}E&&V0(this)},render:function(e,t){if(t.tween._time||!vf())for(var r=t._pt;r;)r.r(e,r.d),r=r._next;else t.styles.revert()},get:Gi,aliases:Ri,getSetter:function(e,t,r){var i=Ri[t];return i&&i.indexOf(",")<0&&(t=i),t in Ki&&t!==Dn&&(e._gsap.x||Gi(e,"x"))?r&&Tp===r?t==="scale"?MT:xT:(Tp=r||{})&&(t==="scale"?ST:bT):e.style&&!rf(e.style[t])?_T:~t.indexOf("-")?vT:mf(e,t)},core:{_removeProperty:Mr,_getMatrix:Mf}};Un.utils.checkPrefix=Xs;Un.core.getStyleSaver=j0;(function(n,e,t,r){var i=Cn(n+","+e+","+t,function(s){Ki[s]=1});Cn(e,function(s){Vn.units[s]="deg",J0[s]=1}),Ri[i[13]]=n+","+e,Cn(r,function(s){var a=s.split(":");Ri[a[1]]=i[a[0]]})})("x,y,z,scale,scaleX,scaleY,xPercent,yPercent","rotation,rotationX,rotationY,skewX,skewY","transform,transformOrigin,svgOrigin,force3D,smoothOrigin,transformPerspective","0:translateX,1:translateY,2:translateZ,8:rotate,8:rotationZ,8:rotateZ,9:rotateX,10:rotateY");Cn("x,y,z,top,right,bottom,left,width,height,fontSize,padding,margin,perspective",function(n){Vn.units[n]="px"});Un.registerPlugin(tg);var ng=Un.registerPlugin(tg)||Un;ng.core.Tween;/**
 * postprocessing v6.39.5 build Wed Sep 09 2026
 * https://github.com/pmndrs/postprocessing
 * Copyright 2015-2026 Raoul van Rüschen
 * @license Zlib
 */var LT=(()=>{const n=new Float32Array([-1,-1,0,3,-1,0,-1,3,0]),e=new Float32Array([0,0,2,0,0,2]),t=new Dt;return t.setAttribute("position",new kt(n,3)),t.setAttribute("uv",new kt(e,2)),t})(),fi=class Ih{static get fullscreenGeometry(){return LT}constructor(e="Pass",t=new uh,r=new Qh){this.name=e,this.renderer=null,this.scene=t,this.camera=r,this.screen=null,this.rtt=!0,this.needsSwap=!0,this.needsDepthBlit=!1,this.needsDepthTexture=!1,this.enabled=!0}get renderToScreen(){return!this.rtt}set renderToScreen(e){if(this.rtt===e){const t=this.fullscreenMaterial;t!==null&&(t.needsUpdate=!0),this.rtt=!e}}set mainScene(e){}set mainCamera(e){}setRenderer(e){this.renderer=e}isEnabled(){return this.enabled}setEnabled(e){this.enabled=e}get fullscreenMaterial(){return this.screen!==null?this.screen.material:null}set fullscreenMaterial(e){let t=this.screen;t!==null?t.material=e:(t=new Wn(Ih.fullscreenGeometry,e),t.frustumCulled=!1,this.scene===null&&(this.scene=new uh),this.scene.add(t),this.screen=t)}getFullscreenMaterial(){return this.fullscreenMaterial}setFullscreenMaterial(e){this.fullscreenMaterial=e}getDepthTexture(){return null}setDepthTexture(e,t=ja){}render(e,t,r,i,s){throw new Error("Render method not implemented!")}setSize(e,t){}initialize(e,t,r){}dispose(){for(const e of Object.keys(this)){const t=this[e];(t instanceof $t||t instanceof Zi||t instanceof Zt||t instanceof Ih)&&this[e].dispose()}this.fullscreenMaterial!==null&&this.fullscreenMaterial.dispose()}},IT=class extends fi{constructor(){super("ClearMaskPass",null,null),this.needsSwap=!1}render(n,e,t,r,i){const s=n.state.buffers.stencil;s.setLocked(!1),s.setTest(!1)}},FT=`#ifdef COLOR_WRITE
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
}`,ig="varying vec2 vUv;void main(){vUv=position.xy*0.5+0.5;gl_Position=vec4(position.xy,1.0,1.0);}",rg=class extends an{constructor(){super({name:"CopyMaterial",defines:{COLOR_SPACE_CONVERSION:"1",DEPTH_PACKING:"0",COLOR_WRITE:"1"},uniforms:{inputBuffer:new gt(null),depthBuffer:new gt(null),channelWeights:new gt(null),opacity:new gt(1)},blending:Sn,toneMapped:!1,depthWrite:!1,depthTest:!1,fragmentShader:FT,vertexShader:ig}),this.depthFunc=il}get inputBuffer(){return this.uniforms.inputBuffer.value}set inputBuffer(n){const e=n!==null;this.colorWrite!==e&&(e?this.defines.COLOR_WRITE=!0:delete this.defines.COLOR_WRITE,this.colorWrite=e,this.needsUpdate=!0),this.uniforms.inputBuffer.value=n}get depthBuffer(){return this.uniforms.depthBuffer.value}set depthBuffer(n){const e=n!==null;this.depthWrite!==e&&(e?this.defines.DEPTH_WRITE=!0:delete this.defines.DEPTH_WRITE,this.depthTest=e,this.depthWrite=e,this.needsUpdate=!0),this.uniforms.depthBuffer.value=n}set depthPacking(n){this.defines.DEPTH_PACKING=n.toFixed(0),this.needsUpdate=!0}get colorSpaceConversion(){return this.defines.COLOR_SPACE_CONVERSION!==void 0}set colorSpaceConversion(n){this.colorSpaceConversion!==n&&(n?this.defines.COLOR_SPACE_CONVERSION=!0:delete this.defines.COLOR_SPACE_CONVERSION,this.needsUpdate=!0)}get channelWeights(){return this.uniforms.channelWeights.value}set channelWeights(n){n!==null?(this.defines.USE_WEIGHTS="1",this.uniforms.channelWeights.value=n):delete this.defines.USE_WEIGHTS,this.needsUpdate=!0}setInputBuffer(n){this.uniforms.inputBuffer.value=n}getOpacity(n){return this.uniforms.opacity.value}setOpacity(n){this.uniforms.opacity.value=n}},NT=class extends fi{constructor(n,e=!0){super("CopyPass"),this.fullscreenMaterial=new rg,this.needsSwap=!1,this.renderTarget=n,n===void 0&&(this.renderTarget=new $t(1,1,{minFilter:zt,magFilter:zt,stencilBuffer:!1,depthBuffer:!1}),this.renderTarget.texture.name="CopyPass.Target"),this.autoResize=e}get resize(){return this.autoResize}set resize(n){this.autoResize=n}get texture(){return this.renderTarget.texture}getTexture(){return this.renderTarget.texture}setAutoResizeEnabled(n){this.autoResize=n}render(n,e,t,r,i){this.fullscreenMaterial.inputBuffer=e.texture,n.setRenderTarget(this.renderToScreen?null:this.renderTarget),n.render(this.scene,this.camera)}setSize(n,e){this.autoResize&&this.renderTarget.setSize(n,e)}initialize(n,e,t){t!==void 0&&(this.renderTarget.texture.type=t,t!==Yt?this.fullscreenMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1":n!==null&&n.outputColorSpace===bt&&(this.renderTarget.texture.colorSpace=bt))}},Lp=new lt,sg=class extends fi{constructor(n=!0,e=!0,t=!1){super("ClearPass",null,null),this.needsSwap=!1,this.color=n,this.depth=e,this.stencil=t,this.overrideClearColor=null,this.overrideClearAlpha=-1}setClearFlags(n,e,t){this.color=n,this.depth=e,this.stencil=t}getOverrideClearColor(){return this.overrideClearColor}setOverrideClearColor(n){this.overrideClearColor=n}getOverrideClearAlpha(){return this.overrideClearAlpha}setOverrideClearAlpha(n){this.overrideClearAlpha=n}render(n,e,t,r,i){const s=this.overrideClearColor,a=this.overrideClearAlpha,o=n.getClearAlpha(),l=s!==null,c=a>=0;l?(n.getClearColor(Lp),n.setClearColor(s,c?a:o)):c&&n.setClearAlpha(a),n.setRenderTarget(this.renderToScreen?null:e),n.clear(this.color,this.depth,this.stencil),l?n.setClearColor(Lp,o):c&&n.setClearAlpha(o)}},OT=class extends fi{constructor(n,e){super("MaskPass",n,e),this.needsSwap=!1,this.clearPass=new sg(!1,!1,!0),this.inverse=!1}set mainScene(n){this.scene=n}set mainCamera(n){this.camera=n}get inverted(){return this.inverse}set inverted(n){this.inverse=n}get clear(){return this.clearPass.enabled}set clear(n){this.clearPass.enabled=n}getClearPass(){return this.clearPass}isInverted(){return this.inverted}setInverted(n){this.inverted=n}render(n,e,t,r,i){const s=n.getContext(),a=n.state.buffers,o=this.scene,l=this.camera,c=this.clearPass,u=this.inverted?0:1,f=1-u;a.color.setMask(!1),a.depth.setMask(!1),a.color.setLocked(!0),a.depth.setLocked(!0),a.stencil.setTest(!0),a.stencil.setOp(s.REPLACE,s.REPLACE,s.REPLACE),a.stencil.setFunc(s.ALWAYS,u,4294967295),a.stencil.setClear(f),a.stencil.setLocked(!0),this.clearPass.enabled&&(this.renderToScreen?c.render(n,null):(c.render(n,e),c.render(n,t))),this.renderToScreen?(n.setRenderTarget(null),n.render(o,l)):(n.setRenderTarget(e),n.render(o,l),n.setRenderTarget(t),n.render(o,l)),a.color.setLocked(!1),a.depth.setLocked(!1),a.stencil.setLocked(!1),a.stencil.setFunc(s.EQUAL,1,4294967295),a.stencil.setOp(s.KEEP,s.KEEP,s.KEEP),a.stencil.setLocked(!0)}};function BT(n,e){const t=n.getContext();if(e<=0||typeof t.renderbufferStorageMultisample!="function")return 0;const r=t.getParameter(t.MAX_SAMPLES),i=Math.min(e,r);if(i<=0)return 0;const s=t.getParameter(t.RENDERBUFFER_BINDING),a=t.createRenderbuffer();try{return t.bindRenderbuffer(t.RENDERBUFFER,a),t.renderbufferStorageMultisample(t.RENDERBUFFER,i,t.RGBA8,1,1),i}catch{return 0}finally{t.bindRenderbuffer(t.RENDERBUFFER,s),t.deleteRenderbuffer(a)}}var jc=1/1e3,kT=1e3,zT=class{constructor(){this.startTime=performance.now(),this.previousTime=0,this.currentTime=0,this._delta=0,this._elapsed=0,this._fixedDelta=1e3/60,this.timescale=1,this.useFixedDelta=!1,this._autoReset=!1}get autoReset(){return this._autoReset}set autoReset(n){typeof document<"u"&&document.hidden!==void 0&&(n?document.addEventListener("visibilitychange",this):document.removeEventListener("visibilitychange",this),this._autoReset=n)}get delta(){return this._delta*jc}get fixedDelta(){return this._fixedDelta*jc}set fixedDelta(n){this._fixedDelta=n*kT}get elapsed(){return this._elapsed*jc}update(n){this.useFixedDelta?this._delta=this.fixedDelta:(this.previousTime=this.currentTime,this.currentTime=(n!==void 0?n:performance.now())-this.startTime,this._delta=this.currentTime-this.previousTime),this._delta*=this.timescale,this._elapsed+=this._delta}reset(){this._delta=0,this._elapsed=0,this.currentTime=performance.now()-this.startTime}getDelta(){return this.delta}getElapsed(){return this.elapsed}handleEvent(n){document.hidden||(this.currentTime=performance.now()-this.startTime)}dispose(){this.autoReset=!1}},GT=class{constructor(n=null,{depthBuffer:e=!0,stencilBuffer:t=!1,multisampling:r=0,frameBufferType:i=Yt}={}){this.renderer=null,this.inputBuffer=this.createBuffer(e,t,i,r),this.outputBuffer=this.inputBuffer.clone(),this.copyPass=new NT,this.depthRenderTarget=null,this.passes=[],this.timer=new zT,this.autoRenderToScreen=!0,this.setRenderer(n)}get stableDepthTexture(){return this.depthRenderTarget===null?null:this.depthRenderTarget.depthTexture}get multisampling(){return this.inputBuffer.samples}set multisampling(n){const e=this.renderer===null?n:BT(this.renderer,n);this.multisampling!==e&&(this.inputBuffer.samples=e,this.outputBuffer.samples=e,this.inputBuffer.dispose(),this.outputBuffer.dispose())}getTimer(){return this.timer}getRenderer(){return this.renderer}setRenderer(n){if(this.renderer=n,n!==null){const e=n.getSize(new We),t=n.getContext().getContextAttributes().alpha,r=this.inputBuffer.texture.type;r===Yt&&n.outputColorSpace===bt&&(this.inputBuffer.texture.colorSpace=bt,this.outputBuffer.texture.colorSpace=bt,this.inputBuffer.dispose(),this.outputBuffer.dispose());const i=this.multisampling;this.multisampling=i,n.autoClear=!1,this.setSize(e.width,e.height);for(const s of this.passes)s.initialize(n,t,r)}}replaceRenderer(n,e=!0){const t=this.renderer,r=t.domElement.parentNode;return this.setRenderer(n),e&&r!==null&&(r.removeChild(t.domElement),r.appendChild(n.domElement)),t}createDepthTexture(){const n=new Wi;n.name="EffectComposer.InputDepth",this.inputBuffer.stencilBuffer?(n.format=cr,n.type=Bs):n.type=li;const e=new Wi;e.format=n.format,e.type=n.type,e.name="EffectComposer.OutputDepth";const t=new Wi;t.format=n.format,t.type=n.type,t.name="EffectComposer.StableDepth",this.inputBuffer.depthTexture=n,this.outputBuffer.depthTexture=e,this.inputBuffer.dispose(),this.outputBuffer.dispose();const{width:r,height:i}=this.inputBuffer;this.depthRenderTarget=new $t(r,i,{depthBuffer:!0,stencilBuffer:this.inputBuffer.stencilBuffer,depthTexture:t})}blitDepthBuffer(n){const e=this.renderer,t=this.depthRenderTarget,r=e.properties,i=e.getContext();e.setRenderTarget(t);const s=r.get(n).__webglFramebuffer,a=r.get(t).__webglFramebuffer,o=n.stencilBuffer?i.DEPTH_BUFFER_BIT|i.STENCIL_BUFFER_BIT:i.DEPTH_BUFFER_BIT;i.bindFramebuffer(i.READ_FRAMEBUFFER,s),i.bindFramebuffer(i.DRAW_FRAMEBUFFER,a),i.blitFramebuffer(0,0,n.width,n.height,0,0,t.width,t.height,o,i.NEAREST),i.bindFramebuffer(i.READ_FRAMEBUFFER,null),i.bindFramebuffer(i.DRAW_FRAMEBUFFER,null),e.setRenderTarget(null)}deleteDepthTexture(){const n=this.stableDepthTexture;for(const e of this.passes)e.getDepthTexture()===n&&e.setDepthTexture(null);this.depthRenderTarget!==null&&(this.depthRenderTarget.dispose(),this.depthRenderTarget=null),this.inputBuffer.depthTexture!==null&&(this.inputBuffer.depthTexture.dispose(),this.inputBuffer.depthTexture=null),this.outputBuffer.depthTexture!==null&&(this.outputBuffer.depthTexture.dispose(),this.outputBuffer.depthTexture=null)}createBuffer(n,e,t,r){const i=this.renderer,s=i===null?new We:i.getDrawingBufferSize(new We),a=new $t(s.width,s.height,{minFilter:zt,magFilter:zt,samples:r,stencilBuffer:e,depthBuffer:n,type:t});return t===Yt&&i!==null&&i.outputColorSpace===bt&&(a.texture.colorSpace=bt),a.texture.name="EffectComposer.Buffer",a.texture.generateMipmaps=!1,a}setMainScene(n){for(const e of this.passes)e.mainScene=n}setMainCamera(n){for(const e of this.passes)e.mainCamera=n}addPass(n,e){const t=this.passes,r=this.renderer,i=r.getDrawingBufferSize(new We),s=r.getContext().getContextAttributes().alpha,a=this.inputBuffer.texture.type;if(n.renderer=r,n.setSize(i.width,i.height),n.initialize(r,s,a),this.autoRenderToScreen&&(t.length>0&&(t[t.length-1].renderToScreen=!1),n.renderToScreen&&(this.autoRenderToScreen=!1)),e!==void 0?t.splice(e,0,n):t.push(n),this.autoRenderToScreen&&(t[t.length-1].renderToScreen=!0),n.needsDepthTexture||this.depthRenderTarget!==null)if(this.depthRenderTarget===null){this.createDepthTexture();for(const o of t)o.setDepthTexture(this.stableDepthTexture)}else n.setDepthTexture(this.stableDepthTexture)}removePass(n){const e=this.passes,t=e.indexOf(n);if(t!==-1&&e.splice(t,1).length>0){const s=this.stableDepthTexture;if(s!==null){const a=(l,c)=>l||c.needsDepthTexture;e.reduce(a,!1)||(n.getDepthTexture()===s&&n.setDepthTexture(null),this.deleteDepthTexture())}this.autoRenderToScreen&&t===e.length&&(n.renderToScreen=!1,e.length>0&&(e[e.length-1].renderToScreen=!0))}}removeAllPasses(){const n=this.passes;this.deleteDepthTexture(),n.length>0&&(this.autoRenderToScreen&&(n[n.length-1].renderToScreen=!1),this.passes=[])}render(n){const e=this.renderer,t=this.copyPass;let r=this.inputBuffer,i=this.outputBuffer,s,a=!1;n===void 0&&(this.timer.update(),n=this.timer.getDelta());for(const o of this.passes)if(o.enabled){if(o.render(e,r,i,n,a),o.needsDepthBlit&&this.depthRenderTarget!==null&&this.blitDepthBuffer(r),o.needsSwap){if(a){t.renderToScreen=o.renderToScreen;const l=e.getContext(),c=e.state.buffers.stencil;c.setFunc(l.NOTEQUAL,1,4294967295),t.render(e,r,i,n,a),c.setFunc(l.EQUAL,1,4294967295)}s=r,r=i,i=s}o instanceof OT?a=!0:o instanceof IT&&(a=!1)}}setSize(n,e,t){const r=this.renderer,i=r.getSize(new We);(n===void 0||e===void 0)&&(n=i.width,e=i.height),(i.width!==n||i.height!==e)&&r.setSize(n,e,t);const s=r.getDrawingBufferSize(new We);this.inputBuffer.setSize(s.width,s.height),this.outputBuffer.setSize(s.width,s.height),this.depthRenderTarget!==null&&this.depthRenderTarget.setSize(s.width,s.height);for(const a of this.passes)a.setSize(s.width,s.height)}reset(){this.dispose(),this.autoRenderToScreen=!0}dispose(){for(const n of this.passes)n.dispose();this.deleteDepthTexture(),this.inputBuffer.dispose(),this.outputBuffer.dispose(),this.copyPass.dispose(),this.timer.dispose(),this.passes=[],fi.fullscreenGeometry.dispose()}},Yr={NONE:0,DEPTH:1,CONVOLUTION:2},pt={FRAGMENT_HEAD:"FRAGMENT_HEAD",FRAGMENT_MAIN_UV:"FRAGMENT_MAIN_UV",FRAGMENT_MAIN_IMAGE:"FRAGMENT_MAIN_IMAGE",VERTEX_HEAD:"VERTEX_HEAD",VERTEX_MAIN_SUPPORT:"VERTEX_MAIN_SUPPORT"},HT=class{constructor(){this.shaderParts=new Map([[pt.FRAGMENT_HEAD,null],[pt.FRAGMENT_MAIN_UV,null],[pt.FRAGMENT_MAIN_IMAGE,null],[pt.VERTEX_HEAD,null],[pt.VERTEX_MAIN_SUPPORT,null]]),this.defines=new Map,this.uniforms=new Map,this.blendModes=new Map,this.extensions=new Set,this.attributes=Yr.NONE,this.varyings=new Set,this.uvTransformation=!1,this.readDepth=!1,this.colorSpace=ks}},Kc=!1,Ip=class{constructor(n=null){this.originalMaterials=new Map,this.material=null,this.materials=null,this.materialsBackSide=null,this.materialsDoubleSide=null,this.materialsFlatShaded=null,this.materialsFlatShadedBackSide=null,this.materialsFlatShadedDoubleSide=null,this.setMaterial(n),this.meshCount=0,this.replaceMaterial=e=>{if(e.isMesh){let t;if(e.material.flatShading)switch(e.material.side){case wn:t=this.materialsFlatShadedDoubleSide;break;case sn:t=this.materialsFlatShadedBackSide;break;default:t=this.materialsFlatShaded;break}else switch(e.material.side){case wn:t=this.materialsDoubleSide;break;case sn:t=this.materialsBackSide;break;default:t=this.materials;break}this.originalMaterials.set(e,e.material),e.isSkinnedMesh?e.material=t[2]:e.isInstancedMesh?e.material=t[1]:e.material=t[0],++this.meshCount}}}cloneMaterial(n){if(!(n instanceof an))return n.clone();const e=n.uniforms,t=new Map;for(const i in e){const s=e[i].value;s.isRenderTargetTexture&&(e[i].value=null,t.set(i,s))}const r=n.clone();for(const i of t)e[i[0]].value=i[1],r.uniforms[i[0]].value=i[1];return r}setMaterial(n){if(this.disposeMaterials(),this.material=n,n!==null){const e=this.materials=[this.cloneMaterial(n),this.cloneMaterial(n),this.cloneMaterial(n)];for(const t of e)t.uniforms=Object.assign({},n.uniforms),t.side=Xi;e[2].skinning=!0,this.materialsBackSide=e.map(t=>{const r=this.cloneMaterial(t);return r.uniforms=Object.assign({},n.uniforms),r.side=sn,r}),this.materialsDoubleSide=e.map(t=>{const r=this.cloneMaterial(t);return r.uniforms=Object.assign({},n.uniforms),r.side=wn,r}),this.materialsFlatShaded=e.map(t=>{const r=this.cloneMaterial(t);return r.uniforms=Object.assign({},n.uniforms),r.flatShading=!0,r}),this.materialsFlatShadedBackSide=e.map(t=>{const r=this.cloneMaterial(t);return r.uniforms=Object.assign({},n.uniforms),r.flatShading=!0,r.side=sn,r}),this.materialsFlatShadedDoubleSide=e.map(t=>{const r=this.cloneMaterial(t);return r.uniforms=Object.assign({},n.uniforms),r.flatShading=!0,r.side=wn,r})}}render(n,e,t){const r=n.shadowMap.enabled;if(n.shadowMap.enabled=!1,Kc){const i=this.originalMaterials;this.meshCount=0,e.traverse(this.replaceMaterial),n.render(e,t);for(const s of i)s[0].material=s[1];this.meshCount!==i.size&&i.clear()}else{const i=e.overrideMaterial;e.overrideMaterial=this.material,n.render(e,t),e.overrideMaterial=i}n.shadowMap.enabled=r}disposeMaterials(){if(this.material!==null){const n=this.materials.concat(this.materialsBackSide).concat(this.materialsDoubleSide).concat(this.materialsFlatShaded).concat(this.materialsFlatShadedBackSide).concat(this.materialsFlatShadedDoubleSide);for(const e of n)e.dispose()}}dispose(){this.originalMaterials.clear(),this.disposeMaterials()}static get workaroundEnabled(){return Kc}static set workaroundEnabled(n){Kc=n}},or=-1,Ci=class extends hi{constructor(n=null,e=or,t=or,r=1){super(),n!==null&&this.addEventListener("change",()=>n.setSize(this.baseSize.width,this.baseSize.height)),this.baseSize=new We(1,1),this.preferredSize=new We(e,t),this.target=this.preferredSize,this.s=r,this.effectiveSize=new We,this.addEventListener("change",()=>this.updateEffectiveSize()),this.updateEffectiveSize()}updateEffectiveSize(){const n=this.baseSize,e=this.preferredSize,t=this.effectiveSize,r=this.scale;e.width!==or?t.width=e.width:e.height!==or?t.width=Math.round(e.height*(n.width/Math.max(n.height,1))):t.width=Math.round(n.width*r),e.height!==or?t.height=e.height:e.width!==or?t.height=Math.round(e.width/Math.max(n.width/Math.max(n.height,1),1)):t.height=Math.round(n.height*r)}get width(){return this.effectiveSize.width}set width(n){this.preferredWidth=n}get height(){return this.effectiveSize.height}set height(n){this.preferredHeight=n}getWidth(){return this.width}getHeight(){return this.height}get scale(){return this.s}set scale(n){this.s!==n&&(this.s=n,this.preferredSize.setScalar(or),this.dispatchEvent({type:"change"}))}getScale(){return this.scale}setScale(n){this.scale=n}get baseWidth(){return this.baseSize.width}set baseWidth(n){this.baseSize.width!==n&&(this.baseSize.width=n,this.dispatchEvent({type:"change"}))}getBaseWidth(){return this.baseWidth}setBaseWidth(n){this.baseWidth=n}get baseHeight(){return this.baseSize.height}set baseHeight(n){this.baseSize.height!==n&&(this.baseSize.height=n,this.dispatchEvent({type:"change"}))}getBaseHeight(){return this.baseHeight}setBaseHeight(n){this.baseHeight=n}setBaseSize(n,e){(this.baseSize.width!==n||this.baseSize.height!==e)&&(this.baseSize.set(n,e),this.dispatchEvent({type:"change"}))}get preferredWidth(){return this.preferredSize.width}set preferredWidth(n){this.preferredSize.width!==n&&(this.preferredSize.width=n,this.dispatchEvent({type:"change"}))}getPreferredWidth(){return this.preferredWidth}setPreferredWidth(n){this.preferredWidth=n}get preferredHeight(){return this.preferredSize.height}set preferredHeight(n){this.preferredSize.height!==n&&(this.preferredSize.height=n,this.dispatchEvent({type:"change"}))}getPreferredHeight(){return this.preferredHeight}setPreferredHeight(n){this.preferredHeight=n}setPreferredSize(n,e){(this.preferredSize.width!==n||this.preferredSize.height!==e)&&(this.preferredSize.set(n,e),this.dispatchEvent({type:"change"}))}copy(n){this.s=n.scale,this.baseSize.set(n.baseWidth,n.baseHeight),this.preferredSize.set(n.preferredWidth,n.preferredHeight),this.dispatchEvent({type:"change"})}static get AUTO_SIZE(){return or}},ot={ADD:0,ALPHA:1,AVERAGE:2,COLOR:3,COLOR_BURN:4,COLOR_DODGE:5,DARKEN:6,DIFFERENCE:7,DIVIDE:8,DST:9,EXCLUSION:10,HARD_LIGHT:11,HARD_MIX:12,HUE:13,INVERT:14,INVERT_RGB:15,LIGHTEN:16,LINEAR_BURN:17,LINEAR_DODGE:18,LINEAR_LIGHT:19,LUMINOSITY:20,MULTIPLY:21,NEGATION:22,NORMAL:23,OVERLAY:24,PIN_LIGHT:25,REFLECT:26,SATURATION:27,SCREEN:28,SOFT_LIGHT:29,SRC:30,SUBTRACT:31,VIVID_LIGHT:32},VT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=dst.rgb+src.rgb;return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",WT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){return mix(dst,src,src.a*opacity);}",XT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=(dst.rgb+src.rgb)*0.5;return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",YT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=RGBToHSL(dst.rgb);vec3 b=RGBToHSL(src.rgb);vec3 c=HSLToRGB(vec3(b.xy,a.z));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",qT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=dst.rgb,b=src.rgb;vec3 c=mix(step(0.0,b)*(1.0-min(vec3(1.0),(1.0-a)/max(b,1e-9))),vec3(1.0),step(1.0,a));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",jT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=dst.rgb,b=src.rgb;vec3 c=step(0.0,a)*mix(min(vec3(1.0),a/max(1.0-b,1e-9)),vec3(1.0),step(1.0,b));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",KT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=min(dst.rgb,src.rgb);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",ZT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=abs(dst.rgb-src.rgb);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",$T="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=dst.rgb/max(src.rgb,1e-9);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",JT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=dst.rgb+src.rgb-2.0*dst.rgb*src.rgb;return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",QT="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=min(dst.rgb,1.0);vec3 b=min(src.rgb,1.0);vec3 c=mix(2.0*a*b,1.0-2.0*(1.0-a)*(1.0-b),step(0.5,b));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",eE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=step(1.0,dst.rgb+src.rgb);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",tE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=RGBToHSL(dst.rgb);vec3 b=RGBToHSL(src.rgb);vec3 c=HSLToRGB(vec3(b.x,a.yz));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",nE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=max(1.0-src.rgb,0.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",iE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=src.rgb*max(1.0-dst.rgb,0.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",rE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=max(dst.rgb,src.rgb);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",sE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=clamp(src.rgb+dst.rgb-1.0,0.0,1.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",aE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=min(dst.rgb+src.rgb,1.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",oE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=clamp(2.0*src.rgb+dst.rgb-1.0,0.0,1.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",lE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=RGBToHSL(dst.rgb);vec3 b=RGBToHSL(src.rgb);vec3 c=HSLToRGB(vec3(a.xy,b.z));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",cE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=dst.rgb*src.rgb;return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",uE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=max(1.0-abs(1.0-dst.rgb-src.rgb),0.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",hE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){return mix(dst,src,opacity);}",fE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=2.0*src.rgb*dst.rgb;vec3 b=1.0-2.0*(1.0-src.rgb)*(1.0-dst.rgb);vec3 c=mix(a,b,step(0.5,dst.rgb));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",dE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 src2=2.0*src.rgb;vec3 c=mix(mix(src2,dst.rgb,step(0.5*dst.rgb,src.rgb)),max(src2-1.0,vec3(0.0)),step(dst.rgb,src2-1.0));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",pE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=min(dst.rgb*dst.rgb/max(1.0-src.rgb,1e-9),1.0);vec3 c=mix(a,src.rgb,step(1.0,src.rgb));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",mE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 a=RGBToHSL(dst.rgb);vec3 b=RGBToHSL(src.rgb);vec3 c=HSLToRGB(vec3(a.x,b.y,a.z));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",gE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=dst.rgb+src.rgb-min(dst.rgb*src.rgb,1.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",_E="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 src2=2.0*src.rgb;vec3 d=dst.rgb+(src2-1.0);vec3 w=step(0.5,src.rgb);vec3 a=dst.rgb-(1.0-src2)*dst.rgb*(1.0-dst.rgb);vec3 b=mix(d*(sqrt(dst.rgb)-dst.rgb),d*dst.rgb*((16.0*dst.rgb-12.0)*dst.rgb+3.0),w*(1.0-step(0.25,dst.rgb)));vec3 c=mix(a,b,w);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",vE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){return src;}",xE="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=max(dst.rgb-src.rgb,0.0);return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",ME="vec4 blend(const in vec4 dst,const in vec4 src,const in float opacity){vec3 c=mix(max(1.0-min((1.0-dst.rgb)/(2.0*src.rgb),1.0),0.0),min(dst.rgb/(2.0*(1.0-src.rgb)),1.0),step(0.5,src.rgb));return mix(dst,vec4(c,max(dst.a,src.a)),opacity);}",SE=new Map([[ot.ADD,VT],[ot.ALPHA,WT],[ot.AVERAGE,XT],[ot.COLOR,YT],[ot.COLOR_BURN,qT],[ot.COLOR_DODGE,jT],[ot.DARKEN,KT],[ot.DIFFERENCE,ZT],[ot.DIVIDE,$T],[ot.DST,null],[ot.EXCLUSION,JT],[ot.HARD_LIGHT,QT],[ot.HARD_MIX,eE],[ot.HUE,tE],[ot.INVERT,nE],[ot.INVERT_RGB,iE],[ot.LIGHTEN,rE],[ot.LINEAR_BURN,sE],[ot.LINEAR_DODGE,aE],[ot.LINEAR_LIGHT,oE],[ot.LUMINOSITY,lE],[ot.MULTIPLY,cE],[ot.NEGATION,uE],[ot.NORMAL,hE],[ot.OVERLAY,fE],[ot.PIN_LIGHT,dE],[ot.REFLECT,pE],[ot.SATURATION,mE],[ot.SCREEN,gE],[ot.SOFT_LIGHT,_E],[ot.SRC,vE],[ot.SUBTRACT,xE],[ot.VIVID_LIGHT,ME]]),bE=class extends hi{constructor(n,e=1){super(),this._blendFunction=n,this.opacity=new gt(e)}getOpacity(){return this.opacity.value}setOpacity(n){this.opacity.value=n}get blendFunction(){return this._blendFunction}set blendFunction(n){this._blendFunction=n,this.dispatchEvent({type:"change"})}getBlendFunction(){return this.blendFunction}setBlendFunction(n){this.blendFunction=n}getShaderCode(){return SE.get(this.blendFunction)}},yE=class extends hi{constructor(n,e,{attributes:t=Yr.NONE,blendFunction:r=ot.NORMAL,defines:i=new Map,uniforms:s=new Map,extensions:a=null,vertexShader:o=null}={}){super(),this.name=n,this.renderer=null,this.attributes=t,this.fragmentShader=e,this.vertexShader=o,this.defines=i,this.uniforms=s,this.extensions=a,this.blendMode=new bE(r),this.blendMode.addEventListener("change",l=>this.setChanged()),this._inputColorSpace=ks,this._outputColorSpace=yi}get inputColorSpace(){return this._inputColorSpace}set inputColorSpace(n){this._inputColorSpace=n,this.setChanged()}get outputColorSpace(){return this._outputColorSpace}set outputColorSpace(n){this._outputColorSpace=n,this.setChanged()}set mainScene(n){}set mainCamera(n){}getName(){return this.name}setRenderer(n){this.renderer=n}getDefines(){return this.defines}getUniforms(){return this.uniforms}getExtensions(){return this.extensions}getBlendMode(){return this.blendMode}getAttributes(){return this.attributes}setAttributes(n){this.attributes=n,this.setChanged()}getFragmentShader(){return this.fragmentShader}setFragmentShader(n){this.fragmentShader=n,this.setChanged()}getVertexShader(){return this.vertexShader}setVertexShader(n){this.vertexShader=n,this.setChanged()}setChanged(){this.dispatchEvent({type:"change"})}setDepthTexture(n,e=ja){}update(n,e,t){}setSize(n,e){}initialize(n,e,t){}dispose(){for(const n of Object.keys(this)){const e=this[n];(e instanceof $t||e instanceof Zi||e instanceof Zt||e instanceof fi)&&this[n].dispose()}}},Sf={MEDIUM:2,LARGE:3},TE=`#ifdef FRAMEBUFFER_PRECISION_HIGH
uniform mediump sampler2D inputBuffer;
#else
uniform lowp sampler2D inputBuffer;
#endif
varying vec2 vUv0;varying vec2 vUv1;varying vec2 vUv2;varying vec2 vUv3;void main(){vec4 sum=texture2D(inputBuffer,vUv0);sum+=texture2D(inputBuffer,vUv1);sum+=texture2D(inputBuffer,vUv2);sum+=texture2D(inputBuffer,vUv3);gl_FragColor=sum*0.25;
#include <colorspace_fragment>
}`,EE="uniform vec4 texelSize;uniform float kernel;uniform float scale;varying vec2 vUv0;varying vec2 vUv1;varying vec2 vUv2;varying vec2 vUv3;void main(){vec2 uv=position.xy*0.5+0.5;vec2 dUv=(texelSize.xy*vec2(kernel)+texelSize.zw)*scale;vUv0=vec2(uv.x-dUv.x,uv.y+dUv.y);vUv1=vec2(uv.x+dUv.x,uv.y+dUv.y);vUv2=vec2(uv.x+dUv.x,uv.y-dUv.y);vUv3=vec2(uv.x-dUv.x,uv.y-dUv.y);gl_Position=vec4(position.xy,1.0,1.0);}",wE=[new Float32Array([0,0]),new Float32Array([0,1,1]),new Float32Array([0,1,1,2]),new Float32Array([0,1,2,2,3]),new Float32Array([0,1,2,3,4,4,5]),new Float32Array([0,1,2,3,4,5,7,8,9,10])],AE=class extends an{constructor(n=new Ct){super({name:"KawaseBlurMaterial",uniforms:{inputBuffer:new gt(null),texelSize:new gt(new Ct),scale:new gt(1),kernel:new gt(0)},blending:Sn,toneMapped:!1,depthWrite:!1,depthTest:!1,fragmentShader:TE,vertexShader:EE}),this.setTexelSize(n.x,n.y),this.kernelSize=Sf.MEDIUM}set inputBuffer(n){this.uniforms.inputBuffer.value=n}setInputBuffer(n){this.inputBuffer=n}get kernelSequence(){return wE[this.kernelSize]}get scale(){return this.uniforms.scale.value}set scale(n){this.uniforms.scale.value=n}getScale(){return this.uniforms.scale.value}setScale(n){this.uniforms.scale.value=n}getKernel(){return null}get kernel(){return this.uniforms.kernel.value}set kernel(n){this.uniforms.kernel.value=n}setKernel(n){this.kernel=n}setTexelSize(n,e){this.uniforms.texelSize.value.set(n,e,n*.5,e*.5)}setSize(n,e){const t=1/n,r=1/e;this.uniforms.texelSize.value.set(t,r,t*.5,r*.5)}},RE=class extends fi{constructor({kernelSize:n=Sf.MEDIUM,resolutionScale:e=.5,width:t=Ci.AUTO_SIZE,height:r=Ci.AUTO_SIZE,resolutionX:i=t,resolutionY:s=r}={}){super("KawaseBlurPass"),this.renderTargetA=new $t(1,1,{depthBuffer:!1}),this.renderTargetA.texture.name="Blur.Target.A",this.renderTargetB=this.renderTargetA.clone(),this.renderTargetB.texture.name="Blur.Target.B";const a=this.resolution=new Ci(this,i,s,e);a.addEventListener("change",o=>this.setSize(a.baseWidth,a.baseHeight)),this._blurMaterial=new AE,this._blurMaterial.kernelSize=n,this.copyMaterial=new rg}getResolution(){return this.resolution}get blurMaterial(){return this._blurMaterial}set blurMaterial(n){this._blurMaterial=n}get dithering(){return this.copyMaterial.dithering}set dithering(n){this.copyMaterial.dithering=n}get kernelSize(){return this.blurMaterial.kernelSize}set kernelSize(n){this.blurMaterial.kernelSize=n}get width(){return this.resolution.width}set width(n){this.resolution.preferredWidth=n}get height(){return this.resolution.height}set height(n){this.resolution.preferredHeight=n}get scale(){return this.blurMaterial.scale}set scale(n){this.blurMaterial.scale=n}getScale(){return this.blurMaterial.scale}setScale(n){this.blurMaterial.scale=n}getKernelSize(){return this.kernelSize}setKernelSize(n){this.kernelSize=n}getResolutionScale(){return this.resolution.scale}setResolutionScale(n){this.resolution.scale=n}render(n,e,t,r,i){const s=this.scene,a=this.camera,o=this.renderTargetA,l=this.renderTargetB,c=this.blurMaterial,u=c.kernelSequence;let f=e;this.fullscreenMaterial=c;for(let h=0,d=u.length;h<d;++h){const m=(h&1)===0?o:l;c.kernel=u[h],c.inputBuffer=f.texture,n.setRenderTarget(m),n.render(s,a),f=m}this.fullscreenMaterial=this.copyMaterial,this.copyMaterial.inputBuffer=f.texture,n.setRenderTarget(this.renderToScreen?null:t),n.render(s,a)}setSize(n,e){const t=this.resolution;t.setBaseSize(n,e);const r=t.width,i=t.height;this.renderTargetA.setSize(r,i),this.renderTargetB.setSize(r,i),this.blurMaterial.setSize(n,e)}initialize(n,e,t){t!==void 0&&(this.renderTargetA.texture.type=t,this.renderTargetB.texture.type=t,t!==Yt?(this.blurMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1",this.copyMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1"):n!==null&&n.outputColorSpace===bt&&(this.renderTargetA.texture.colorSpace=bt,this.renderTargetB.texture.colorSpace=bt))}static get AUTO_SIZE(){return Ci.AUTO_SIZE}},CE=`#include <common>
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
}`,PE=class extends an{constructor(n=!1,e=null){super({name:"LuminanceMaterial",defines:{THREE_REVISION:qa.replace(/\D+/g,"")},uniforms:{inputBuffer:new gt(null),threshold:new gt(0),smoothing:new gt(1),range:new gt(null)},blending:Sn,toneMapped:!1,depthWrite:!1,depthTest:!1,fragmentShader:CE,vertexShader:ig}),this.colorOutput=n,this.luminanceRange=e}set inputBuffer(n){this.uniforms.inputBuffer.value=n}setInputBuffer(n){this.uniforms.inputBuffer.value=n}get threshold(){return this.uniforms.threshold.value}set threshold(n){this.smoothing>0||n>0?this.defines.THRESHOLD="1":delete this.defines.THRESHOLD,this.uniforms.threshold.value=n}getThreshold(){return this.threshold}setThreshold(n){this.threshold=n}get smoothing(){return this.uniforms.smoothing.value}set smoothing(n){this.threshold>0||n>0?this.defines.THRESHOLD="1":delete this.defines.THRESHOLD,this.uniforms.smoothing.value=n}getSmoothingFactor(){return this.smoothing}setSmoothingFactor(n){this.smoothing=n}get useThreshold(){return this.threshold>0||this.smoothing>0}set useThreshold(n){}get colorOutput(){return this.defines.COLOR!==void 0}set colorOutput(n){n?this.defines.COLOR="1":delete this.defines.COLOR,this.needsUpdate=!0}isColorOutputEnabled(n){return this.colorOutput}setColorOutputEnabled(n){this.colorOutput=n}get useRange(){return this.luminanceRange!==null}set useRange(n){this.luminanceRange=null}get luminanceRange(){return this.uniforms.range.value}set luminanceRange(n){n!==null?this.defines.RANGE="1":delete this.defines.RANGE,this.uniforms.range.value=n,this.needsUpdate=!0}getLuminanceRange(){return this.luminanceRange}setLuminanceRange(n){this.luminanceRange=n}},DE=class extends fi{constructor({renderTarget:n,luminanceRange:e,colorOutput:t,resolutionScale:r=1,width:i=Ci.AUTO_SIZE,height:s=Ci.AUTO_SIZE,resolutionX:a=i,resolutionY:o=s}={}){super("LuminancePass"),this.fullscreenMaterial=new PE(t,e),this.needsSwap=!1,this.renderTarget=n,this.renderTarget===void 0&&(this.renderTarget=new $t(1,1,{depthBuffer:!1}),this.renderTarget.texture.name="LuminancePass.Target");const l=this.resolution=new Ci(this,a,o,r);l.addEventListener("change",c=>this.setSize(l.baseWidth,l.baseHeight))}get texture(){return this.renderTarget.texture}getTexture(){return this.renderTarget.texture}getResolution(){return this.resolution}render(n,e,t,r,i){const s=this.fullscreenMaterial;s.inputBuffer=e.texture,n.setRenderTarget(this.renderToScreen?null:this.renderTarget),n.render(this.scene,this.camera)}setSize(n,e){const t=this.resolution;t.setBaseSize(n,e),this.renderTarget.setSize(t.width,t.height)}initialize(n,e,t){t!==void 0&&t!==Yt&&(this.renderTarget.texture.type=t,this.fullscreenMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1")}},UE=`#ifdef FRAMEBUFFER_PRECISION_HIGH
uniform mediump sampler2D inputBuffer;
#else
uniform lowp sampler2D inputBuffer;
#endif
#define WEIGHT_INNER 0.125
#define WEIGHT_OUTER 0.05556
varying vec2 vUv;varying vec2 vUv00;varying vec2 vUv01;varying vec2 vUv02;varying vec2 vUv03;varying vec2 vUv04;varying vec2 vUv05;varying vec2 vUv06;varying vec2 vUv07;varying vec2 vUv08;varying vec2 vUv09;varying vec2 vUv10;varying vec2 vUv11;float clampToBorder(const in vec2 uv){return float(uv.s>=0.0&&uv.s<=1.0&&uv.t>=0.0&&uv.t<=1.0);}void main(){vec4 c=vec4(0.0);vec4 w=WEIGHT_INNER*vec4(clampToBorder(vUv00),clampToBorder(vUv01),clampToBorder(vUv02),clampToBorder(vUv03));c+=w.x*texture2D(inputBuffer,vUv00);c+=w.y*texture2D(inputBuffer,vUv01);c+=w.z*texture2D(inputBuffer,vUv02);c+=w.w*texture2D(inputBuffer,vUv03);w=WEIGHT_OUTER*vec4(clampToBorder(vUv04),clampToBorder(vUv05),clampToBorder(vUv06),clampToBorder(vUv07));c+=w.x*texture2D(inputBuffer,vUv04);c+=w.y*texture2D(inputBuffer,vUv05);c+=w.z*texture2D(inputBuffer,vUv06);c+=w.w*texture2D(inputBuffer,vUv07);w=WEIGHT_OUTER*vec4(clampToBorder(vUv08),clampToBorder(vUv09),clampToBorder(vUv10),clampToBorder(vUv11));c+=w.x*texture2D(inputBuffer,vUv08);c+=w.y*texture2D(inputBuffer,vUv09);c+=w.z*texture2D(inputBuffer,vUv10);c+=w.w*texture2D(inputBuffer,vUv11);c+=WEIGHT_OUTER*texture2D(inputBuffer,vUv);gl_FragColor=c;
#include <colorspace_fragment>
}`,LE="uniform vec2 texelSize;varying vec2 vUv;varying vec2 vUv00;varying vec2 vUv01;varying vec2 vUv02;varying vec2 vUv03;varying vec2 vUv04;varying vec2 vUv05;varying vec2 vUv06;varying vec2 vUv07;varying vec2 vUv08;varying vec2 vUv09;varying vec2 vUv10;varying vec2 vUv11;void main(){vUv=position.xy*0.5+0.5;vUv00=vUv+texelSize*vec2(-1.0,1.0);vUv01=vUv+texelSize*vec2(1.0,1.0);vUv02=vUv+texelSize*vec2(-1.0,-1.0);vUv03=vUv+texelSize*vec2(1.0,-1.0);vUv04=vUv+texelSize*vec2(-2.0,2.0);vUv05=vUv+texelSize*vec2(0.0,2.0);vUv06=vUv+texelSize*vec2(2.0,2.0);vUv07=vUv+texelSize*vec2(-2.0,0.0);vUv08=vUv+texelSize*vec2(2.0,0.0);vUv09=vUv+texelSize*vec2(-2.0,-2.0);vUv10=vUv+texelSize*vec2(0.0,-2.0);vUv11=vUv+texelSize*vec2(2.0,-2.0);gl_Position=vec4(position.xy,1.0,1.0);}",IE=class extends an{constructor(){super({name:"DownsamplingMaterial",uniforms:{inputBuffer:new gt(null),texelSize:new gt(new We)},blending:Sn,toneMapped:!1,depthWrite:!1,depthTest:!1,fragmentShader:UE,vertexShader:LE})}set inputBuffer(n){this.uniforms.inputBuffer.value=n}setSize(n,e){this.uniforms.texelSize.value.set(1/n,1/e)}},FE=`#ifdef FRAMEBUFFER_PRECISION_HIGH
uniform mediump sampler2D inputBuffer;uniform mediump sampler2D supportBuffer;
#else
uniform lowp sampler2D inputBuffer;uniform lowp sampler2D supportBuffer;
#endif
uniform float radius;varying vec2 vUv;varying vec2 vUv0;varying vec2 vUv1;varying vec2 vUv2;varying vec2 vUv3;varying vec2 vUv4;varying vec2 vUv5;varying vec2 vUv6;varying vec2 vUv7;void main(){vec4 c=vec4(0.0);c+=texture2D(inputBuffer,vUv0)*0.0625;c+=texture2D(inputBuffer,vUv1)*0.125;c+=texture2D(inputBuffer,vUv2)*0.0625;c+=texture2D(inputBuffer,vUv3)*0.125;c+=texture2D(inputBuffer,vUv)*0.25;c+=texture2D(inputBuffer,vUv4)*0.125;c+=texture2D(inputBuffer,vUv5)*0.0625;c+=texture2D(inputBuffer,vUv6)*0.125;c+=texture2D(inputBuffer,vUv7)*0.0625;vec4 baseColor=texture2D(supportBuffer,vUv);gl_FragColor=mix(baseColor,c,radius);
#include <colorspace_fragment>
}`,NE="uniform vec2 texelSize;varying vec2 vUv;varying vec2 vUv0;varying vec2 vUv1;varying vec2 vUv2;varying vec2 vUv3;varying vec2 vUv4;varying vec2 vUv5;varying vec2 vUv6;varying vec2 vUv7;void main(){vUv=position.xy*0.5+0.5;vUv0=vUv+texelSize*vec2(-1.0,1.0);vUv1=vUv+texelSize*vec2(0.0,1.0);vUv2=vUv+texelSize*vec2(1.0,1.0);vUv3=vUv+texelSize*vec2(-1.0,0.0);vUv4=vUv+texelSize*vec2(1.0,0.0);vUv5=vUv+texelSize*vec2(-1.0,-1.0);vUv6=vUv+texelSize*vec2(0.0,-1.0);vUv7=vUv+texelSize*vec2(1.0,-1.0);gl_Position=vec4(position.xy,1.0,1.0);}",OE=class extends an{constructor(){super({name:"UpsamplingMaterial",uniforms:{inputBuffer:new gt(null),supportBuffer:new gt(null),texelSize:new gt(new We),radius:new gt(.85)},blending:Sn,toneMapped:!1,depthWrite:!1,depthTest:!1,fragmentShader:FE,vertexShader:NE})}set inputBuffer(n){this.uniforms.inputBuffer.value=n}set supportBuffer(n){this.uniforms.supportBuffer.value=n}get radius(){return this.uniforms.radius.value}set radius(n){this.uniforms.radius.value=n}setSize(n,e){this.uniforms.texelSize.value.set(1/n,1/e)}},BE=class extends fi{constructor(){super("MipmapBlurPass"),this.needsSwap=!1,this.renderTarget=new $t(1,1,{depthBuffer:!1}),this.renderTarget.texture.name="Upsampling.Mipmap0",this.downsamplingMipmaps=[],this.upsamplingMipmaps=[],this.downsamplingMaterial=new IE,this.upsamplingMaterial=new OE,this.resolution=new We}get texture(){return this.renderTarget.texture}get levels(){return this.downsamplingMipmaps.length}set levels(n){if(this.levels!==n){const e=this.renderTarget;this.dispose(),this.downsamplingMipmaps=[],this.upsamplingMipmaps=[];for(let t=0;t<n;++t){const r=e.clone();r.texture.name="Downsampling.Mipmap"+t,this.downsamplingMipmaps.push(r)}this.upsamplingMipmaps.push(e);for(let t=1,r=n-1;t<r;++t){const i=e.clone();i.texture.name="Upsampling.Mipmap"+t,this.upsamplingMipmaps.push(i)}this.setSize(this.resolution.x,this.resolution.y)}}get radius(){return this.upsamplingMaterial.radius}set radius(n){this.upsamplingMaterial.radius=n}render(n,e,t,r,i){const{scene:s,camera:a}=this,{downsamplingMaterial:o,upsamplingMaterial:l}=this,{downsamplingMipmaps:c,upsamplingMipmaps:u}=this;let f=e;this.fullscreenMaterial=o;for(let h=0,d=c.length;h<d;++h){const m=c[h];o.setSize(f.width,f.height),o.inputBuffer=f.texture,n.setRenderTarget(m),n.render(s,a),f=m}this.fullscreenMaterial=l;for(let h=u.length-1;h>=0;--h){const d=u[h];l.setSize(f.width,f.height),l.inputBuffer=f.texture,l.supportBuffer=c[h].texture,n.setRenderTarget(d),n.render(s,a),f=d}}setSize(n,e){const t=this.resolution;t.set(n,e);let r=t.width,i=t.height;for(let s=0,a=this.downsamplingMipmaps.length;s<a;++s)r=Math.round(r*.5),i=Math.round(i*.5),this.downsamplingMipmaps[s].setSize(r,i),s<this.upsamplingMipmaps.length&&this.upsamplingMipmaps[s].setSize(r,i)}initialize(n,e,t){if(t!==void 0){const r=this.downsamplingMipmaps.concat(this.upsamplingMipmaps);for(const i of r)i.texture.type=t;if(t!==Yt)this.downsamplingMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1",this.upsamplingMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1";else if(n!==null&&n.outputColorSpace===bt)for(const i of r)i.texture.colorSpace=bt}}dispose(){super.dispose();for(const n of this.downsamplingMipmaps.concat(this.upsamplingMipmaps))n.dispose()}},kE=`#ifdef FRAMEBUFFER_PRECISION_HIGH
uniform mediump sampler2D map;
#else
uniform lowp sampler2D map;
#endif
uniform float intensity;void mainImage(const in vec4 inputColor,const in vec2 uv,out vec4 outputColor){outputColor=texture2D(map,uv)*intensity;}`,zE=class extends yE{constructor({blendFunction:n=ot.SCREEN,luminanceThreshold:e=1,luminanceSmoothing:t=.03,mipmapBlur:r=!0,intensity:i=1,radius:s=.85,levels:a=8,kernelSize:o=Sf.LARGE,resolutionScale:l=.5,width:c=Ci.AUTO_SIZE,height:u=Ci.AUTO_SIZE,resolutionX:f=c,resolutionY:h=u}={}){super("BloomEffect",kE,{blendFunction:n,uniforms:new Map([["map",new gt(null)],["intensity",new gt(i)]])}),this.renderTarget=new $t(1,1,{depthBuffer:!1}),this.renderTarget.texture.name="Bloom.Target",this.blurPass=new RE({kernelSize:o}),this.luminancePass=new DE({colorOutput:!0}),this.luminanceMaterial.threshold=e,this.luminanceMaterial.smoothing=t,this.mipmapBlurPass=new BE,this.mipmapBlurPass.enabled=r,this.mipmapBlurPass.radius=s,this.mipmapBlurPass.levels=a,this.uniforms.get("map").value=r?this.mipmapBlurPass.texture:this.renderTarget.texture;const d=this.resolution=new Ci(this,f,h,l);d.addEventListener("change",m=>this.setSize(d.baseWidth,d.baseHeight))}get texture(){return this.mipmapBlurPass.enabled?this.mipmapBlurPass.texture:this.renderTarget.texture}getTexture(){return this.texture}getResolution(){return this.resolution}getBlurPass(){return this.blurPass}getLuminancePass(){return this.luminancePass}get luminanceMaterial(){return this.luminancePass.fullscreenMaterial}getLuminanceMaterial(){return this.luminancePass.fullscreenMaterial}get width(){return this.resolution.width}set width(n){this.resolution.preferredWidth=n}get height(){return this.resolution.height}set height(n){this.resolution.preferredHeight=n}get dithering(){return this.blurPass.dithering}set dithering(n){this.blurPass.dithering=n}get kernelSize(){return this.blurPass.kernelSize}set kernelSize(n){this.blurPass.kernelSize=n}get distinction(){return console.warn(this.name,"distinction was removed"),1}set distinction(n){console.warn(this.name,"distinction was removed")}get intensity(){return this.uniforms.get("intensity").value}set intensity(n){this.uniforms.get("intensity").value=n}getIntensity(){return this.intensity}setIntensity(n){this.intensity=n}getResolutionScale(){return this.resolution.scale}setResolutionScale(n){this.resolution.scale=n}update(n,e,t){const r=this.renderTarget,i=this.luminancePass;i.enabled?(i.render(n,e),this.mipmapBlurPass.enabled?this.mipmapBlurPass.render(n,i.renderTarget):this.blurPass.render(n,i.renderTarget,r)):this.mipmapBlurPass.enabled?this.mipmapBlurPass.render(n,e):this.blurPass.render(n,e,r)}setSize(n,e){const t=this.resolution;t.setBaseSize(n,e),this.renderTarget.setSize(t.width,t.height),this.blurPass.resolution.copy(t),this.luminancePass.setSize(n,e),this.mipmapBlurPass.setSize(n,e)}initialize(n,e,t){this.blurPass.initialize(n,e,t),this.luminancePass.initialize(n,e,t),this.mipmapBlurPass.initialize(n,e,t),t!==void 0&&(this.renderTarget.texture.type=t,n!==null&&n.outputColorSpace===bt&&(this.renderTarget.texture.colorSpace=bt))}},GE=class extends fi{constructor(n,e,t=null){super("RenderPass",n,e),this.needsSwap=!1,this.needsDepthBlit=!0,this.clearPass=new sg,this.overrideMaterialManager=t===null?null:new Ip(t),this.ignoreBackground=!1,this.skipShadowMapUpdate=!1,this.selection=null}set mainScene(n){this.scene=n}set mainCamera(n){this.camera=n}get renderToScreen(){return super.renderToScreen}set renderToScreen(n){super.renderToScreen=n,this.clearPass.renderToScreen=n}get overrideMaterial(){const n=this.overrideMaterialManager;return n!==null?n.material:null}set overrideMaterial(n){const e=this.overrideMaterialManager;n!==null?e!==null?e.setMaterial(n):this.overrideMaterialManager=new Ip(n):e!==null&&(e.dispose(),this.overrideMaterialManager=null)}getOverrideMaterial(){return this.overrideMaterial}setOverrideMaterial(n){this.overrideMaterial=n}get clear(){return this.clearPass.enabled}set clear(n){this.clearPass.enabled=n}getSelection(){return this.selection}setSelection(n){this.selection=n}isBackgroundDisabled(){return this.ignoreBackground}setBackgroundDisabled(n){this.ignoreBackground=n}isShadowMapDisabled(){return this.skipShadowMapUpdate}setShadowMapDisabled(n){this.skipShadowMapUpdate=n}getClearPass(){return this.clearPass}render(n,e,t,r,i){const s=this.scene,a=this.camera,o=this.selection,l=a.layers.mask,c=s.background,u=n.shadowMap.autoUpdate,f=this.renderToScreen?null:e;o!==null&&a.layers.set(o.getLayer()),this.skipShadowMapUpdate&&(n.shadowMap.autoUpdate=!1),(this.ignoreBackground||this.clearPass.overrideClearColor!==null)&&(s.background=null),this.clearPass.enabled&&this.clearPass.render(n,e),n.setRenderTarget(f),this.overrideMaterialManager!==null?this.overrideMaterialManager.render(n,s,a):n.render(s,a),a.layers.mask=l,s.background=c,n.shadowMap.autoUpdate=u}},HE=`#include <common>
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
}`,VE="uniform vec2 resolution;uniform vec2 texelSize;uniform float cameraNear;uniform float cameraFar;uniform float aspect;uniform float time;varying vec2 vUv;VERTEX_HEAD void main(){vUv=position.xy*0.5+0.5;VERTEX_MAIN_SUPPORT gl_Position=vec4(position.xy,1.0,1.0);}",WE=class extends an{constructor(n,e,t,r,i=!1){super({name:"EffectMaterial",defines:{THREE_REVISION:qa.replace(/\D+/g,""),DEPTH_PACKING:"0",ENCODE_OUTPUT:"1"},uniforms:{inputBuffer:new gt(null),depthBuffer:new gt(null),resolution:new gt(new We),texelSize:new gt(new We),cameraNear:new gt(.3),cameraFar:new gt(1e3),aspect:new gt(1),time:new gt(0)},blending:Sn,toneMapped:!1,depthWrite:!1,depthTest:!1,dithering:i}),n&&this.setShaderParts(n),e&&this.setDefines(e),t&&this.setUniforms(t),this.copyCameraSettings(r)}set inputBuffer(n){this.uniforms.inputBuffer.value=n}setInputBuffer(n){this.uniforms.inputBuffer.value=n}get depthBuffer(){return this.uniforms.depthBuffer.value}set depthBuffer(n){this.uniforms.depthBuffer.value=n}get depthPacking(){return Number(this.defines.DEPTH_PACKING)}set depthPacking(n){this.defines.DEPTH_PACKING=n.toFixed(0),this.needsUpdate=!0}setDepthBuffer(n,e=ja){this.depthBuffer=n,this.depthPacking=e}setShaderData(n){this.setShaderParts(n.shaderParts),this.setDefines(n.defines),this.setUniforms(n.uniforms),this.setExtensions(n.extensions)}setShaderParts(n){return this.fragmentShader=HE.replace(pt.FRAGMENT_HEAD,n.get(pt.FRAGMENT_HEAD)||"").replace(pt.FRAGMENT_MAIN_UV,n.get(pt.FRAGMENT_MAIN_UV)||"").replace(pt.FRAGMENT_MAIN_IMAGE,n.get(pt.FRAGMENT_MAIN_IMAGE)||""),this.vertexShader=VE.replace(pt.VERTEX_HEAD,n.get(pt.VERTEX_HEAD)||"").replace(pt.VERTEX_MAIN_SUPPORT,n.get(pt.VERTEX_MAIN_SUPPORT)||""),this.needsUpdate=!0,this}setDefines(n){for(const e of n.entries())this.defines[e[0]]=e[1];return this.needsUpdate=!0,this}setUniforms(n){for(const e of n.entries())this.uniforms[e[0]]=e[1];return this}setExtensions(n){this.extensions={};for(const e of n)this.extensions[e]=!0;return this}get encodeOutput(){return this.defines.ENCODE_OUTPUT!==void 0}set encodeOutput(n){this.encodeOutput!==n&&(n?this.defines.ENCODE_OUTPUT="1":delete this.defines.ENCODE_OUTPUT,this.needsUpdate=!0)}isOutputEncodingEnabled(n){return this.encodeOutput}setOutputEncodingEnabled(n){this.encodeOutput=n}get time(){return this.uniforms.time.value}set time(n){this.uniforms.time.value=n}setDeltaTime(n){this.uniforms.time.value+=n}adoptCameraSettings(n){this.copyCameraSettings(n)}copyCameraSettings(n){n&&(this.uniforms.cameraNear.value=n.near,this.uniforms.cameraFar.value=n.far,n instanceof kn?this.defines.PERSPECTIVE_CAMERA="1":delete this.defines.PERSPECTIVE_CAMERA,this.needsUpdate=!0)}setSize(n,e){const t=this.uniforms;t.resolution.value.set(n,e),t.texelSize.value.set(1/n,1/e),t.aspect.value=n/e}static get Section(){return pt}};function Fp(n,e,t){for(const r of e){const i="$1"+n+r.charAt(0).toUpperCase()+r.slice(1),s=new RegExp("([^\\.])(\\b"+r+"\\b)","g");for(const a of t.entries())a[1]!==null&&t.set(a[0],a[1].replace(s,i))}}function XE(n,e,t){let r=e.getFragmentShader(),i=e.getVertexShader();const s=r!==void 0&&/mainImage/.test(r),a=r!==void 0&&/mainUv/.test(r);if(t.attributes|=e.getAttributes(),r===void 0)throw new Error(`Missing fragment shader (${e.name})`);if(a&&(t.attributes&Yr.CONVOLUTION)!==0)throw new Error(`Effects that transform UVs are incompatible with convolution effects (${e.name})`);if(!s&&!a)throw new Error(`Could not find mainImage or mainUv function (${e.name})`);{const o=/\w+\s+(\w+)\([\w\s,]*\)\s*{/g,l=t.shaderParts;let c=l.get(pt.FRAGMENT_HEAD)||"",u=l.get(pt.FRAGMENT_MAIN_UV)||"",f=l.get(pt.FRAGMENT_MAIN_IMAGE)||"",h=l.get(pt.VERTEX_HEAD)||"",d=l.get(pt.VERTEX_MAIN_SUPPORT)||"";const m=new Set,g=new Set;if(a&&(u+=`	${n}MainUv(UV);
`,t.uvTransformation=!0),i!==null&&/mainSupport/.test(i)){const M=/mainSupport *\([\w\s]*?uv\s*?\)/.test(i);d+=`	${n}MainSupport(`,d+=M?`vUv);
`:`);
`;for(const y of i.matchAll(/(?:varying\s+\w+\s+([\S\s]*?);)/g))for(const v of y[1].split(/\s*,\s*/))t.varyings.add(v),m.add(v),g.add(v);for(const y of i.matchAll(o))g.add(y[1])}for(const M of r.matchAll(o))g.add(M[1]);for(const M of e.defines.keys())g.add(M.replace(/\([\w\s,]*\)/g,""));for(const M of e.uniforms.keys())g.add(M);g.delete("while"),g.delete("for"),g.delete("if"),e.uniforms.forEach((M,y)=>t.uniforms.set(n+y.charAt(0).toUpperCase()+y.slice(1),M)),e.defines.forEach((M,y)=>t.defines.set(n+y.charAt(0).toUpperCase()+y.slice(1),M));const p=new Map([["fragment",r],["vertex",i]]);Fp(n,g,t.defines),Fp(n,g,p),r=p.get("fragment"),i=p.get("vertex");const _=e.blendMode;if(t.blendModes.set(_.blendFunction,_),s){e.inputColorSpace!==null&&e.inputColorSpace!==t.colorSpace&&(f+=e.inputColorSpace===bt?`color0 = sRGBTransferOETF(color0);
	`:`color0 = sRGBToLinear(color0);
	`),e.outputColorSpace!==yi?t.colorSpace=e.outputColorSpace:e.inputColorSpace!==null&&(t.colorSpace=e.inputColorSpace);const M=/MainImage *\([\w\s,]*?depth[\w\s,]*?\)/;f+=`${n}MainImage(color0, UV, `,(t.attributes&Yr.DEPTH)!==0&&M.test(r)&&(f+="depth, ",t.readDepth=!0),f+=`color1);
	`;const y=n+"BlendOpacity";t.uniforms.set(y,_.opacity),f+=`color0 = blend${_.blendFunction}(color0, color1, ${y});

	`,c+=`uniform float ${y};

`}if(c+=r+`
`,i!==null&&(h+=i+`
`),l.set(pt.FRAGMENT_HEAD,c),l.set(pt.FRAGMENT_MAIN_UV,u),l.set(pt.FRAGMENT_MAIN_IMAGE,f),l.set(pt.VERTEX_HEAD,h),l.set(pt.VERTEX_MAIN_SUPPORT,d),e.extensions!==null)for(const M of e.extensions)t.extensions.add(M)}}var YE=class extends fi{constructor(n,...e){super("EffectPass"),this.fullscreenMaterial=new WE(null,null,null,n),this.listener=t=>this.handleEvent(t),this.effects=[],this.setEffects(e),this.skipRendering=!1,this.minTime=1,this.maxTime=Number.POSITIVE_INFINITY,this.timeScale=1}set mainScene(n){for(const e of this.effects)e.mainScene=n}set mainCamera(n){this.fullscreenMaterial.copyCameraSettings(n);for(const e of this.effects)e.mainCamera=n}get encodeOutput(){return this.fullscreenMaterial.encodeOutput}set encodeOutput(n){this.fullscreenMaterial.encodeOutput=n}get dithering(){return this.fullscreenMaterial.dithering}set dithering(n){const e=this.fullscreenMaterial;e.dithering=n,e.needsUpdate=!0}setEffects(n){for(const e of this.effects)e.removeEventListener("change",this.listener);this.effects=n.sort((e,t)=>t.attributes-e.attributes);for(const e of this.effects)e.addEventListener("change",this.listener)}updateMaterial(){const n=new HT;let e=0;for(const a of this.effects)if(a.blendMode.blendFunction===ot.DST)n.attributes|=a.getAttributes()&Yr.DEPTH;else{if((n.attributes&a.getAttributes()&Yr.CONVOLUTION)!==0)throw new Error(`Convolution effects cannot be merged (${a.name})`);XE("e"+e++,a,n)}let t=n.shaderParts.get(pt.FRAGMENT_HEAD),r=n.shaderParts.get(pt.FRAGMENT_MAIN_IMAGE),i=n.shaderParts.get(pt.FRAGMENT_MAIN_UV);const s=/\bblend\b/g;for(const a of n.blendModes.values())t+=a.getShaderCode().replace(s,`blend${a.blendFunction}`)+`
`;(n.attributes&Yr.DEPTH)!==0?(n.readDepth&&(r=`float depth = readDepth(UV);

	`+r),this.needsDepthTexture=this.getDepthTexture()===null):this.needsDepthTexture=!1,n.colorSpace===bt&&(r+=`color0 = sRGBToLinear(color0);
	`),n.uvTransformation?(i=`vec2 transformedUv = vUv;
`+i,n.defines.set("UV","transformedUv")):n.defines.set("UV","vUv"),n.shaderParts.set(pt.FRAGMENT_HEAD,t),n.shaderParts.set(pt.FRAGMENT_MAIN_IMAGE,r),n.shaderParts.set(pt.FRAGMENT_MAIN_UV,i);for(const[a,o]of n.shaderParts)o!==null&&n.shaderParts.set(a,o.trim().replace(/^#/,`
#`));this.skipRendering=e===0,this.needsSwap=!this.skipRendering,this.fullscreenMaterial.setShaderData(n)}recompile(){this.updateMaterial()}getDepthTexture(){return this.fullscreenMaterial.depthBuffer}setDepthTexture(n,e=ja){this.fullscreenMaterial.depthBuffer=n,this.fullscreenMaterial.depthPacking=e;for(const t of this.effects)t.setDepthTexture(n,e)}render(n,e,t,r,i){for(const s of this.effects)s.update(n,e,r);if(!this.skipRendering||this.renderToScreen){const s=this.fullscreenMaterial;s.inputBuffer=e.texture,s.time+=r*this.timeScale,n.setRenderTarget(this.renderToScreen?null:t),n.render(this.scene,this.camera)}}setSize(n,e){this.fullscreenMaterial.setSize(n,e);for(const t of this.effects)t.setSize(n,e)}initialize(n,e,t){this.renderer=n;for(const r of this.effects)r.initialize(n,e,t);this.updateMaterial(),t!==void 0&&t!==Yt&&(this.fullscreenMaterial.defines.FRAMEBUFFER_PRECISION_HIGH="1")}dispose(){super.dispose();for(const n of this.effects)n.removeEventListener("change",this.listener),n.dispose()}handleEvent(n){switch(n.type){case"change":this.recompile();break}}};const ag=(n,e)=>{if(typeof n=="number"){if(e===3)return{mode:"rgb",r:(n>>8&15|n>>4&240)/255,g:(n>>4&15|n&240)/255,b:(n&15|n<<4&240)/255};if(e===4)return{mode:"rgb",r:(n>>12&15|n>>8&240)/255,g:(n>>8&15|n>>4&240)/255,b:(n>>4&15|n&240)/255,alpha:(n&15|n<<4&240)/255};if(e===6)return{mode:"rgb",r:(n>>16&255)/255,g:(n>>8&255)/255,b:(n&255)/255};if(e===8)return{mode:"rgb",r:(n>>24&255)/255,g:(n>>16&255)/255,b:(n>>8&255)/255,alpha:(n&255)/255}}},qE={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},jE=n=>ag(qE[n.toLowerCase()],6),KE=/^#?([0-9a-f]{8}|[0-9a-f]{6}|[0-9a-f]{4}|[0-9a-f]{3})$/i,ZE=n=>{let e;return(e=n.match(KE))?ag(parseInt(e[1],16),e[1].length):void 0},_r="([+-]?\\d*\\.?\\d+(?:[eE][+-]?\\d+)?)",Fa=`${_r}%`,bf=`(?:${_r}%|${_r})`,$E=`(?:${_r}(deg|grad|rad|turn)|${_r})`,Ys="\\s*,\\s*",JE=new RegExp(`^rgba?\\(\\s*${_r}${Ys}${_r}${Ys}${_r}\\s*(?:,\\s*${bf}\\s*)?\\)$`),QE=new RegExp(`^rgba?\\(\\s*${Fa}${Ys}${Fa}${Ys}${Fa}\\s*(?:,\\s*${bf}\\s*)?\\)$`),e2=n=>{let e={mode:"rgb"},t;if(t=n.match(JE))t[1]!==void 0&&(e.r=t[1]/255),t[2]!==void 0&&(e.g=t[2]/255),t[3]!==void 0&&(e.b=t[3]/255);else if(t=n.match(QE))t[1]!==void 0&&(e.r=t[1]/100),t[2]!==void 0&&(e.g=t[2]/100),t[3]!==void 0&&(e.b=t[3]/100);else return;return t[4]!==void 0?e.alpha=Math.max(0,Math.min(1,t[4]/100)):t[5]!==void 0&&(e.alpha=Math.max(0,Math.min(1,+t[5]))),e},t2=(n,e)=>n===void 0?void 0:typeof n!="object"?u2(n):n.mode!==void 0?n:e?{...n,mode:e}:void 0,yf=(n="rgb")=>e=>(e=t2(e,n))!==void 0?e.mode===n?e:wi[e.mode][n]?wi[e.mode][n](e):n==="rgb"?wi[e.mode].rgb(e):wi.rgb[n](wi[e.mode].rgb(e)):void 0,wi={},og={},Ml=[],lg={},n2=n=>n,vt=n=>(wi[n.mode]={...wi[n.mode],...n.toMode},Object.keys(n.fromMode||{}).forEach(e=>{wi[e]||(wi[e]={}),wi[e][n.mode]=n.fromMode[e]}),n.ranges||(n.ranges={}),n.difference||(n.difference={}),n.channels.forEach(e=>{if(n.ranges[e]===void 0&&(n.ranges[e]=[0,1]),!n.interpolate[e])throw new Error(`Missing interpolator for: ${e}`);typeof n.interpolate[e]=="function"&&(n.interpolate[e]={use:n.interpolate[e]}),n.interpolate[e].fixup||(n.interpolate[e].fixup=n2)}),og[n.mode]=n,(n.parse||[]).forEach(e=>{i2(e,n.mode)}),yf(n.mode)),cg=n=>og[n],i2=(n,e)=>{if(typeof n=="string"){if(!e)throw new Error("'mode' required when 'parser' is a string");lg[n]=e}else typeof n=="function"&&Ml.indexOf(n)<0&&Ml.push(n)},Fh=/[^\x00-\x7F]|[a-zA-Z_]/,r2=/[^\x00-\x7F]|[-\w]/,Ee={Function:"function",Ident:"ident",Number:"number",Percentage:"percentage",ParenClose:")",None:"none",Hue:"hue",Alpha:"alpha"};let Je=0;function ko(n){let e=n[Je],t=n[Je+1];return e==="-"||e==="+"?/\d/.test(t)||t==="."&&/\d/.test(n[Je+2]):e==="."?/\d/.test(t):/\d/.test(e)}function Nh(n){if(Je>=n.length)return!1;let e=n[Je];if(Fh.test(e))return!0;if(e==="-"){if(n.length-Je<2)return!1;let t=n[Je+1];return!!(t==="-"||Fh.test(t))}return!1}const s2={deg:1,rad:180/Math.PI,grad:9/10,turn:360};function ba(n){let e="";if((n[Je]==="-"||n[Je]==="+")&&(e+=n[Je++]),e+=zo(n),n[Je]==="."&&/\d/.test(n[Je+1])&&(e+=n[Je++]+zo(n)),(n[Je]==="e"||n[Je]==="E")&&((n[Je+1]==="-"||n[Je+1]==="+")&&/\d/.test(n[Je+2])?e+=n[Je++]+n[Je++]+zo(n):/\d/.test(n[Je+1])&&(e+=n[Je++]+zo(n))),Nh(n)){let t=Sl(n);return t==="deg"||t==="rad"||t==="turn"||t==="grad"?{type:Ee.Hue,value:e*s2[t]}:void 0}return n[Je]==="%"?(Je++,{type:Ee.Percentage,value:+e}):{type:Ee.Number,value:+e}}function zo(n){let e="";for(;/\d/.test(n[Je]);)e+=n[Je++];return e}function Sl(n){let e="";for(;Je<n.length&&r2.test(n[Je]);)e+=n[Je++];return e}function a2(n){let e=Sl(n);return n[Je]==="("?(Je++,{type:Ee.Function,value:e}):e==="none"?{type:Ee.None,value:void 0}:{type:Ee.Ident,value:e}}function o2(n=""){let e=n.trim(),t=[],r;for(Je=0;Je<e.length;){if(r=e[Je++],r===`
`||r==="	"||r===" "){for(;Je<e.length&&(e[Je]===`
`||e[Je]==="	"||e[Je]===" ");)Je++;continue}if(r===",")return;if(r===")"){t.push({type:Ee.ParenClose});continue}if(r==="+"){if(Je--,ko(e)){t.push(ba(e));continue}return}if(r==="-"){if(Je--,ko(e)){t.push(ba(e));continue}if(Nh(e)){t.push({type:Ee.Ident,value:Sl(e)});continue}return}if(r==="."){if(Je--,ko(e)){t.push(ba(e));continue}return}if(r==="/"){for(;Je<e.length&&(e[Je]===`
`||e[Je]==="	"||e[Je]===" ");)Je++;let i;if(ko(e)&&(i=ba(e),i.type!==Ee.Hue)){t.push({type:Ee.Alpha,value:i});continue}if(Nh(e)&&Sl(e)==="none"){t.push({type:Ee.Alpha,value:{type:Ee.None,value:void 0}});continue}return}if(/\d/.test(r)){Je--,t.push(ba(e));continue}if(Fh.test(r)){Je--,t.push(a2(e));continue}return}return t}function l2(n){n._i=0;let e=n[n._i++];if(!e||e.type!==Ee.Function||e.value!=="color"||(e=n[n._i++],e.type!==Ee.Ident))return;const t=lg[e.value];if(!t)return;const r={mode:t},i=ug(n,!1);if(!i)return;const s=cg(t).channels;for(let a=0,o,l;a<s.length;a++)o=i[a],l=s[a],o.type!==Ee.None&&(r[l]=o.type===Ee.Number?o.value:o.value/100,l==="alpha"&&(r[l]=Math.max(0,Math.min(1,r[l]))));return r}function ug(n,e){const t=[];let r;for(;n._i<n.length;){if(r=n[n._i++],r.type===Ee.None||r.type===Ee.Number||r.type===Ee.Alpha||r.type===Ee.Percentage||e&&r.type===Ee.Hue){t.push(r);continue}if(r.type===Ee.ParenClose){if(n._i<n.length)return;continue}return}if(!(t.length<3||t.length>4)){if(t.length===4){if(t[3].type!==Ee.Alpha)return;t[3]=t[3].value}return t.length===3&&t.push({type:Ee.None,value:void 0}),t.every(i=>i.type!==Ee.Alpha)?t:void 0}}function c2(n,e){n._i=0;let t=n[n._i++];if(!t||t.type!==Ee.Function)return;let r=ug(n,e);if(r)return r.unshift(t.value),r}const u2=n=>{if(typeof n!="string")return;const e=o2(n),t=e?c2(e,!0):void 0;let r,i=0,s=Ml.length;for(;i<s;)if((r=Ml[i++](n,t))!==void 0)return r;return e?l2(e):void 0};function h2(n,e){if(!e||e[0]!=="rgb"&&e[0]!=="rgba")return;const t={mode:"rgb"},[,r,i,s,a]=e;if(!(r.type===Ee.Hue||i.type===Ee.Hue||s.type===Ee.Hue))return r.type!==Ee.None&&(t.r=r.type===Ee.Number?r.value/255:r.value/100),i.type!==Ee.None&&(t.g=i.type===Ee.Number?i.value/255:i.value/100),s.type!==Ee.None&&(t.b=s.type===Ee.Number?s.value/255:s.value/100),a.type!==Ee.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ee.Number?a.value:a.value/100))),t}const f2=n=>n==="transparent"?{mode:"rgb",r:0,g:0,b:0,alpha:0}:void 0,d2=(n,e,t)=>n+t*(e-n),p2=n=>{let e=[];for(let t=0;t<n.length-1;t++){let r=n[t],i=n[t+1];r===void 0&&i===void 0?e.push(void 0):r!==void 0&&i!==void 0?e.push([r,i]):e.push(r!==void 0?[r,r]:[i,i])}return e},m2=n=>e=>{let t=p2(e);return r=>{let i=r*t.length,s=r>=1?t.length-1:Math.max(Math.floor(i),0),a=t[s];return a===void 0?void 0:n(a[0],a[1],i-s)}},Oe=m2(d2),en=n=>{let e=!1,t=n.map(r=>r!==void 0?(e=!0,r):1);return e?t:n},$s={mode:"rgb",channels:["r","g","b","alpha"],parse:[h2,ZE,e2,jE,f2,"srgb"],serialize:"srgb",interpolate:{r:Oe,g:Oe,b:Oe,alpha:{use:Oe,fixup:en}},gamut:!0,white:{r:1,g:1,b:1},black:{r:0,g:0,b:0}},Zc=(n=0)=>Math.pow(Math.abs(n),563/256)*Math.sign(n),Np=n=>{let e=Zc(n.r),t=Zc(n.g),r=Zc(n.b),i={mode:"xyz65",x:.5766690429101305*e+.1855582379065463*t+.1882286462349947*r,y:.297344975250536*e+.6273635662554661*t+.0752914584939979*r,z:.0270313613864123*e+.0706888525358272*t+.9913375368376386*r};return n.alpha!==void 0&&(i.alpha=n.alpha),i},$c=n=>Math.pow(Math.abs(n),256/563)*Math.sign(n),Op=({x:n,y:e,z:t,alpha:r})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let i={mode:"a98",r:$c(n*2.0415879038107465-e*.5650069742788597-.3447313507783297*t),g:$c(n*-.9692436362808798+e*1.8759675015077206+.0415550574071756*t),b:$c(n*.0134442806320312-e*.1183623922310184+1.0151749943912058*t)};return r!==void 0&&(i.alpha=r),i},Jc=(n=0)=>{const e=Math.abs(n);return e<=.04045?n/12.92:(Math.sign(n)||1)*Math.pow((e+.055)/1.055,2.4)},Js=({r:n,g:e,b:t,alpha:r})=>{let i={mode:"lrgb",r:Jc(n),g:Jc(e),b:Jc(t)};return r!==void 0&&(i.alpha=r),i},Qr=n=>{let{r:e,g:t,b:r,alpha:i}=Js(n),s={mode:"xyz65",x:.4123907992659593*e+.357584339383878*t+.1804807884018343*r,y:.2126390058715102*e+.715168678767756*t+.0721923153607337*r,z:.0193308187155918*e+.119194779794626*t+.9505321522496607*r};return i!==void 0&&(s.alpha=i),s},Qc=(n=0)=>{const e=Math.abs(n);return e>.0031308?(Math.sign(n)||1)*(1.055*Math.pow(e,1/2.4)-.055):n*12.92},Qs=({r:n,g:e,b:t,alpha:r},i="rgb")=>{let s={mode:i,r:Qc(n),g:Qc(e),b:Qc(t)};return r!==void 0&&(s.alpha=r),s},es=({x:n,y:e,z:t,alpha:r})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let i=Qs({r:n*3.2409699419045226-e*1.537383177570094-.4986107602930034*t,g:n*-.9692436362808796+e*1.8759675015077204+.0415550574071756*t,b:n*.0556300796969936-e*.2039769588889765+1.0569715142428784*t});return r!==void 0&&(i.alpha=r),i},g2={...$s,mode:"a98",parse:["a98-rgb"],serialize:"a98-rgb",fromMode:{rgb:n=>Op(Qr(n)),xyz65:Op},toMode:{rgb:n=>es(Np(n)),xyz65:Np}},hn=n=>(n=n%360)<0?n+360:n,_2=(n,e)=>n.map((t,r,i)=>{if(t===void 0)return t;let s=hn(t);return r===0||n[r-1]===void 0?s:e(s-hn(i[r-1]))}).reduce((t,r)=>!t.length||r===void 0||t[t.length-1]===void 0?(t.push(r),t):(t.push(r+t[t.length-1]),t),[]),$i=n=>_2(n,e=>Math.abs(e)<=180?e:e-360*Math.sign(e)),rn=[-.14861,1.78277,-.29227,-.90649,1.97294,0],v2=Math.PI/180,x2=180/Math.PI;let Bp=rn[3]*rn[4],kp=rn[1]*rn[4],zp=rn[1]*rn[2]-rn[0]*rn[3];const M2=({r:n,g:e,b:t,alpha:r})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let i=(zp*t+n*Bp-e*kp)/(zp+Bp-kp),s=t-i,a=(rn[4]*(e-i)-rn[2]*s)/rn[3],o={mode:"cubehelix",l:i,s:i===0||i===1?void 0:Math.sqrt(s*s+a*a)/(rn[4]*i*(1-i))};return o.s&&(o.h=Math.atan2(a,s)*x2-120),r!==void 0&&(o.alpha=r),o},S2=({h:n,s:e,l:t,alpha:r})=>{let i={mode:"rgb"};n=(n===void 0?0:n+120)*v2,t===void 0&&(t=0);let s=e===void 0?0:e*t*(1-t),a=Math.cos(n),o=Math.sin(n);return i.r=t+s*(rn[0]*a+rn[1]*o),i.g=t+s*(rn[2]*a+rn[3]*o),i.b=t+s*(rn[4]*a+rn[5]*o),r!==void 0&&(i.alpha=r),i},Fl=(n,e)=>{if(n.h===void 0||e.h===void 0||!n.s||!e.s)return 0;let t=hn(n.h),r=hn(e.h),i=Math.sin((r-t+360)/2*Math.PI/180);return 2*Math.sqrt(n.s*e.s)*i},b2=(n,e)=>{if(n.h===void 0||e.h===void 0)return 0;let t=hn(n.h),r=hn(e.h);return Math.abs(r-t)>180?t-(r-360*Math.sign(r-t)):r-t},Nl=(n,e)=>{if(n.h===void 0||e.h===void 0||!n.c||!e.c)return 0;let t=hn(n.h),r=hn(e.h),i=Math.sin((r-t+360)/2*Math.PI/180);return 2*Math.sqrt(n.c*e.c)*i},Ji=n=>{let e=n.reduce((r,i)=>{if(i!==void 0){let s=i*Math.PI/180;r.sin+=Math.sin(s),r.cos+=Math.cos(s)}return r},{sin:0,cos:0}),t=Math.atan2(e.sin,e.cos)*180/Math.PI;return t<0?360+t:t},y2={mode:"cubehelix",channels:["h","s","l","alpha"],parse:["--cubehelix"],serialize:"--cubehelix",ranges:{h:[0,360],s:[0,4.614],l:[0,1]},fromMode:{rgb:M2},toMode:{rgb:S2},interpolate:{h:{use:Oe,fixup:$i},s:Oe,l:Oe,alpha:{use:Oe,fixup:en}},difference:{h:Fl},average:{h:Ji}},br=({l:n,a:e,b:t,alpha:r},i="lch")=>{e===void 0&&(e=0),t===void 0&&(t=0);let s=Math.sqrt(e*e+t*t),a={mode:i,l:n,c:s};return s&&(a.h=hn(Math.atan2(t,e)*180/Math.PI)),r!==void 0&&(a.alpha=r),a},yr=({l:n,c:e,h:t,alpha:r},i="lab")=>{t===void 0&&(t=0);let s={mode:i,l:n,a:e?e*Math.cos(t/180*Math.PI):0,b:e?e*Math.sin(t/180*Math.PI):0};return r!==void 0&&(s.alpha=r),s},hg=Math.pow(29,3)/Math.pow(3,3),fg=Math.pow(6,3)/Math.pow(29,3),qt={X:.3457/.3585,Y:1,Z:(1-.3457-.3585)/.3585},Fs={X:.3127/.329,Y:1,Z:(1-.3127-.329)/.329};let eu=n=>Math.pow(n,3)>fg?Math.pow(n,3):(116*n-16)/hg;const dg=({l:n,a:e,b:t,alpha:r})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let i=(n+16)/116,s=e/500+i,a=i-t/200,o={mode:"xyz65",x:eu(s)*Fs.X,y:eu(i)*Fs.Y,z:eu(a)*Fs.Z};return r!==void 0&&(o.alpha=r),o},Ol=n=>es(dg(n)),tu=n=>n>fg?Math.cbrt(n):(hg*n+16)/116,pg=({x:n,y:e,z:t,alpha:r})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let i=tu(n/Fs.X),s=tu(e/Fs.Y),a=tu(t/Fs.Z),o={mode:"lab65",l:116*s-16,a:500*(i-s),b:200*(s-a)};return r!==void 0&&(o.alpha=r),o},Bl=n=>{let e=pg(Qr(n));return n.r===n.b&&n.b===n.g&&(e.a=e.b=0),e},bl=1,mg=1,Ya=26/180*Math.PI,yl=Math.cos(Ya),Tl=Math.sin(Ya),gg=100/Math.log(139/100),Oh=({l:n,c:e,h:t,alpha:r})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let i={mode:"lab65",l:(Math.exp(n*bl/gg)-1)/.0039},s=(Math.exp(.0435*e*mg*bl)-1)/.075,a=s*Math.cos(t/180*Math.PI-Ya),o=s*Math.sin(t/180*Math.PI-Ya);return i.a=a*yl-o/.83*Tl,i.b=a*Tl+o/.83*yl,r!==void 0&&(i.alpha=r),i},Bh=({l:n,a:e,b:t,alpha:r})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let i=e*yl+t*Tl,s=.83*(t*yl-e*Tl),a=Math.sqrt(i*i+s*s),o={mode:"dlch",l:gg/bl*Math.log(1+.0039*n),c:Math.log(1+.075*a)/(.0435*mg*bl)};return o.c&&(o.h=hn((Math.atan2(s,i)+Ya)/Math.PI*180)),r!==void 0&&(o.alpha=r),o},Gp=n=>Oh(br(n,"dlch")),Hp=n=>yr(Bh(n),"dlab"),T2={mode:"dlab",parse:["--din99o-lab"],serialize:"--din99o-lab",toMode:{lab65:Gp,rgb:n=>Ol(Gp(n))},fromMode:{lab65:Hp,rgb:n=>Hp(Bl(n))},channels:["l","a","b","alpha"],ranges:{l:[0,100],a:[-40.09,45.501],b:[-40.469,44.344]},interpolate:{l:Oe,a:Oe,b:Oe,alpha:{use:Oe,fixup:en}}},E2={mode:"dlch",parse:["--din99o-lch"],serialize:"--din99o-lch",toMode:{lab65:Oh,dlab:n=>yr(n,"dlab"),rgb:n=>Ol(Oh(n))},fromMode:{lab65:Bh,dlab:n=>br(n,"dlch"),rgb:n=>Bh(Bl(n))},channels:["l","c","h","alpha"],ranges:{l:[0,100],c:[0,51.484],h:[0,360]},interpolate:{l:Oe,c:Oe,h:{use:Oe,fixup:$i},alpha:{use:Oe,fixup:en}},difference:{h:Nl},average:{h:Ji}};function w2({h:n,s:e,i:t,alpha:r}){n=hn(n!==void 0?n:0),e===void 0&&(e=0),t===void 0&&(t=0);let i=Math.abs(n/60%2-1),s;switch(Math.floor(n/60)){case 0:s={r:t*(1+e*(3/(2-i)-1)),g:t*(1+e*(3*(1-i)/(2-i)-1)),b:t*(1-e)};break;case 1:s={r:t*(1+e*(3*(1-i)/(2-i)-1)),g:t*(1+e*(3/(2-i)-1)),b:t*(1-e)};break;case 2:s={r:t*(1-e),g:t*(1+e*(3/(2-i)-1)),b:t*(1+e*(3*(1-i)/(2-i)-1))};break;case 3:s={r:t*(1-e),g:t*(1+e*(3*(1-i)/(2-i)-1)),b:t*(1+e*(3/(2-i)-1))};break;case 4:s={r:t*(1+e*(3*(1-i)/(2-i)-1)),g:t*(1-e),b:t*(1+e*(3/(2-i)-1))};break;case 5:s={r:t*(1+e*(3/(2-i)-1)),g:t*(1-e),b:t*(1+e*(3*(1-i)/(2-i)-1))};break;default:s={r:t*(1-e),g:t*(1-e),b:t*(1-e)}}return s.mode="rgb",r!==void 0&&(s.alpha=r),s}function A2({r:n,g:e,b:t,alpha:r}){n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let i=Math.max(n,e,t),s=Math.min(n,e,t),a={mode:"hsi",s:n+e+t===0?0:1-3*s/(n+e+t),i:(n+e+t)/3};return i-s!==0&&(a.h=(i===n?(e-t)/(i-s)+(e<t)*6:i===e?(t-n)/(i-s)+2:(n-e)/(i-s)+4)*60),r!==void 0&&(a.alpha=r),a}const R2={mode:"hsi",toMode:{rgb:w2},parse:["--hsi"],serialize:"--hsi",fromMode:{rgb:A2},channels:["h","s","i","alpha"],ranges:{h:[0,360]},gamut:"rgb",interpolate:{h:{use:Oe,fixup:$i},s:Oe,i:Oe,alpha:{use:Oe,fixup:en}},difference:{h:Fl},average:{h:Ji}};function C2({h:n,s:e,l:t,alpha:r}){n=hn(n!==void 0?n:0),e===void 0&&(e=0),t===void 0&&(t=0);let i=t+e*(t<.5?t:1-t),s=i-(i-t)*2*Math.abs(n/60%2-1),a;switch(Math.floor(n/60)){case 0:a={r:i,g:s,b:2*t-i};break;case 1:a={r:s,g:i,b:2*t-i};break;case 2:a={r:2*t-i,g:i,b:s};break;case 3:a={r:2*t-i,g:s,b:i};break;case 4:a={r:s,g:2*t-i,b:i};break;case 5:a={r:i,g:2*t-i,b:s};break;default:a={r:2*t-i,g:2*t-i,b:2*t-i}}return a.mode="rgb",r!==void 0&&(a.alpha=r),a}function P2({r:n,g:e,b:t,alpha:r}){n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let i=Math.max(n,e,t),s=Math.min(n,e,t),a={mode:"hsl",s:i===s?0:(i-s)/(1-Math.abs(i+s-1)),l:.5*(i+s)};return i-s!==0&&(a.h=(i===n?(e-t)/(i-s)+(e<t)*6:i===e?(t-n)/(i-s)+2:(n-e)/(i-s)+4)*60),r!==void 0&&(a.alpha=r),a}const D2=(n,e)=>{switch(e){case"deg":return+n;case"rad":return n/Math.PI*180;case"grad":return n/10*9;case"turn":return n*360}},U2=new RegExp(`^hsla?\\(\\s*${$E}${Ys}${Fa}${Ys}${Fa}\\s*(?:,\\s*${bf}\\s*)?\\)$`),L2=n=>{let e=n.match(U2);if(!e)return;let t={mode:"hsl"};return e[3]!==void 0?t.h=+e[3]:e[1]!==void 0&&e[2]!==void 0&&(t.h=D2(e[1],e[2])),e[4]!==void 0&&(t.s=Math.min(Math.max(0,e[4]/100),1)),e[5]!==void 0&&(t.l=Math.min(Math.max(0,e[5]/100),1)),e[6]!==void 0?t.alpha=Math.max(0,Math.min(1,e[6]/100)):e[7]!==void 0&&(t.alpha=Math.max(0,Math.min(1,+e[7]))),t};function I2(n,e){if(!e||e[0]!=="hsl"&&e[0]!=="hsla")return;const t={mode:"hsl"},[,r,i,s,a]=e;if(r.type!==Ee.None){if(r.type===Ee.Percentage)return;t.h=r.value}if(i.type!==Ee.None){if(i.type===Ee.Hue)return;t.s=i.value/100}if(s.type!==Ee.None){if(s.type===Ee.Hue)return;t.l=s.value/100}return a.type!==Ee.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ee.Number?a.value:a.value/100))),t}const _g={mode:"hsl",toMode:{rgb:C2},fromMode:{rgb:P2},channels:["h","s","l","alpha"],ranges:{h:[0,360]},gamut:"rgb",parse:[I2,L2],serialize:n=>`hsl(${n.h!==void 0?n.h:"none"} ${n.s!==void 0?n.s*100+"%":"none"} ${n.l!==void 0?n.l*100+"%":"none"}${n.alpha<1?` / ${n.alpha}`:""})`,interpolate:{h:{use:Oe,fixup:$i},s:Oe,l:Oe,alpha:{use:Oe,fixup:en}},difference:{h:Fl},average:{h:Ji}};function vg({h:n,s:e,v:t,alpha:r}){n=hn(n!==void 0?n:0),e===void 0&&(e=0),t===void 0&&(t=0);let i=Math.abs(n/60%2-1),s;switch(Math.floor(n/60)){case 0:s={r:t,g:t*(1-e*i),b:t*(1-e)};break;case 1:s={r:t*(1-e*i),g:t,b:t*(1-e)};break;case 2:s={r:t*(1-e),g:t,b:t*(1-e*i)};break;case 3:s={r:t*(1-e),g:t*(1-e*i),b:t};break;case 4:s={r:t*(1-e*i),g:t*(1-e),b:t};break;case 5:s={r:t,g:t*(1-e),b:t*(1-e*i)};break;default:s={r:t*(1-e),g:t*(1-e),b:t*(1-e)}}return s.mode="rgb",r!==void 0&&(s.alpha=r),s}function xg({r:n,g:e,b:t,alpha:r}){n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let i=Math.max(n,e,t),s=Math.min(n,e,t),a={mode:"hsv",s:i===0?0:1-s/i,v:i};return i-s!==0&&(a.h=(i===n?(e-t)/(i-s)+(e<t)*6:i===e?(t-n)/(i-s)+2:(n-e)/(i-s)+4)*60),r!==void 0&&(a.alpha=r),a}const Mg={mode:"hsv",toMode:{rgb:vg},parse:["--hsv"],serialize:"--hsv",fromMode:{rgb:xg},channels:["h","s","v","alpha"],ranges:{h:[0,360]},gamut:"rgb",interpolate:{h:{use:Oe,fixup:$i},s:Oe,v:Oe,alpha:{use:Oe,fixup:en}},difference:{h:Fl},average:{h:Ji}};function F2({h:n,w:e,b:t,alpha:r}){if(e===void 0&&(e=0),t===void 0&&(t=0),e+t>1){let i=e+t;e/=i,t/=i}return vg({h:n,s:t===1?1:1-e/(1-t),v:1-t,alpha:r})}function N2(n){let e=xg(n);if(e===void 0)return;let t=e.s!==void 0?e.s:0,r=e.v!==void 0?e.v:0,i={mode:"hwb",w:(1-t)*r,b:1-r};return e.h!==void 0&&(i.h=e.h),e.alpha!==void 0&&(i.alpha=e.alpha),i}function O2(n,e){if(!e||e[0]!=="hwb")return;const t={mode:"hwb"},[,r,i,s,a]=e;if(r.type!==Ee.None){if(r.type===Ee.Percentage)return;t.h=r.value}if(i.type!==Ee.None){if(i.type===Ee.Hue)return;t.w=i.value/100}if(s.type!==Ee.None){if(s.type===Ee.Hue)return;t.b=s.value/100}return a.type!==Ee.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ee.Number?a.value:a.value/100))),t}const B2={mode:"hwb",toMode:{rgb:F2},fromMode:{rgb:N2},channels:["h","w","b","alpha"],ranges:{h:[0,360]},gamut:"rgb",parse:[O2],serialize:n=>`hwb(${n.h!==void 0?n.h:"none"} ${n.w!==void 0?n.w*100+"%":"none"} ${n.b!==void 0?n.b*100+"%":"none"}${n.alpha<1?` / ${n.alpha}`:""})`,interpolate:{h:{use:Oe,fixup:$i},w:Oe,b:Oe,alpha:{use:Oe,fixup:en}},difference:{h:b2},average:{h:Ji}},Sg=203,kl=.1593017578125,bg=78.84375,zl=.8359375,Gl=18.8515625,Hl=18.6875;function nu(n){if(n<0)return 0;const e=Math.pow(n,1/bg);return 1e4*Math.pow(Math.max(0,e-zl)/(Gl-Hl*e),1/kl)}function iu(n){if(n<0)return 0;const e=Math.pow(n/1e4,kl);return Math.pow((zl+Gl*e)/(1+Hl*e),bg)}const ru=n=>Math.max(n/Sg,0),Vp=({i:n,t:e,p:t,alpha:r})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);const i=nu(n+.008609037037932761*e+.11102962500302593*t),s=nu(n-.00860903703793275*e-.11102962500302599*t),a=nu(n+.5600313357106791*e-.32062717498731885*t),o={mode:"xyz65",x:ru(2.070152218389422*i-1.3263473389671556*s+.2066510476294051*a),y:ru(.3647385209748074*i+.680566024947227*s-.0453045459220346*a),z:ru(-.049747207535812*i-.0492609666966138*s+1.1880659249923042*a)};return r!==void 0&&(o.alpha=r),o},su=(n=0)=>Math.max(n*Sg,0),Wp=({x:n,y:e,z:t,alpha:r})=>{const i=su(n),s=su(e),a=su(t),o=iu(.3592832590121217*i+.6976051147779502*s-.0358915932320289*a),l=iu(-.1920808463704995*i+1.1004767970374323*s+.0753748658519118*a),c=iu(.0070797844607477*i+.0748396662186366*s+.8433265453898765*a),u=.5*o+.5*l,f=1.61376953125*o-3.323486328125*l+1.709716796875*c,h=4.378173828125*o-4.24560546875*l-.132568359375*c,d={mode:"itp",i:u,t:f,p:h};return r!==void 0&&(d.alpha=r),d},k2={mode:"itp",channels:["i","t","p","alpha"],parse:["--ictcp"],serialize:"--ictcp",toMode:{xyz65:Vp,rgb:n=>es(Vp(n))},fromMode:{xyz65:Wp,rgb:n=>Wp(Qr(n))},ranges:{i:[0,.581],t:[-.369,.272],p:[-.164,.331]},interpolate:{i:Oe,t:Oe,p:Oe,alpha:{use:Oe,fixup:en}}},z2=134.03437499999998,G2=16295499532821565e-27,au=n=>{if(n<0)return 0;let e=Math.pow(n/1e4,kl);return Math.pow((zl+Gl*e)/(1+Hl*e),z2)},ou=(n=0)=>Math.max(n*203,0),yg=({x:n,y:e,z:t,alpha:r})=>{n=ou(n),e=ou(e),t=ou(t);let i=1.15*n-.15*t,s=.66*e+.34*n,a=au(.41478972*i+.579999*s+.014648*t),o=au(-.20151*i+1.120649*s+.0531008*t),l=au(-.0166008*i+.2648*s+.6684799*t),c=(a+o)/2,u={mode:"jab",j:.44*c/(1-.56*c)-G2,a:3.524*a-4.066708*o+.542708*l,b:.199076*a+1.096799*o-1.295875*l};return r!==void 0&&(u.alpha=r),u},H2=134.03437499999998,Xp=16295499532821565e-27,lu=n=>{if(n<0)return 0;let e=Math.pow(n,1/H2);return 1e4*Math.pow((zl-e)/(Hl*e-Gl),1/kl)},cu=n=>n/203,Tg=({j:n,a:e,b:t,alpha:r})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let i=(n+Xp)/(.44+.56*(n+Xp)),s=lu(i+.13860504*e+.058047316*t),a=lu(i-.13860504*e-.058047316*t),o=lu(i-.096019242*e-.8118919*t),l={mode:"xyz65",x:cu(1.661373024652174*s-.914523081304348*a+.23136208173913045*o),y:cu(-.3250758611844533*s+1.571847026732543*a-.21825383453227928*o),z:cu(-.090982811*s-.31272829*a+1.5227666*o)};return r!==void 0&&(l.alpha=r),l},Eg=n=>{let e=yg(Qr(n));return n.r===n.b&&n.b===n.g&&(e.a=e.b=0),e},wg=n=>es(Tg(n)),V2={mode:"jab",channels:["j","a","b","alpha"],parse:["--jzazbz"],serialize:"--jzazbz",fromMode:{rgb:Eg,xyz65:yg},toMode:{rgb:wg,xyz65:Tg},ranges:{j:[0,.222],a:[-.109,.129],b:[-.185,.134]},interpolate:{j:Oe,a:Oe,b:Oe,alpha:{use:Oe,fixup:en}}},Yp=({j:n,a:e,b:t,alpha:r})=>{e===void 0&&(e=0),t===void 0&&(t=0);let i=Math.sqrt(e*e+t*t),s={mode:"jch",j:n,c:i};return i&&(s.h=hn(Math.atan2(t,e)*180/Math.PI)),r!==void 0&&(s.alpha=r),s},qp=({j:n,c:e,h:t,alpha:r})=>{t===void 0&&(t=0);let i={mode:"jab",j:n,a:e?e*Math.cos(t/180*Math.PI):0,b:e?e*Math.sin(t/180*Math.PI):0};return r!==void 0&&(i.alpha=r),i},W2={mode:"jch",parse:["--jzczhz"],serialize:"--jzczhz",toMode:{jab:qp,rgb:n=>wg(qp(n))},fromMode:{rgb:n=>Yp(Eg(n)),jab:Yp},channels:["j","c","h","alpha"],ranges:{j:[0,.221],c:[0,.19],h:[0,360]},interpolate:{h:{use:Oe,fixup:$i},c:Oe,j:Oe,alpha:{use:Oe,fixup:en}},difference:{h:Nl},average:{h:Ji}},Vl=Math.pow(29,3)/Math.pow(3,3),Tf=Math.pow(6,3)/Math.pow(29,3);let uu=n=>Math.pow(n,3)>Tf?Math.pow(n,3):(116*n-16)/Vl;const Ef=({l:n,a:e,b:t,alpha:r})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let i=(n+16)/116,s=e/500+i,a=i-t/200,o={mode:"xyz50",x:uu(s)*qt.X,y:uu(i)*qt.Y,z:uu(a)*qt.Z};return r!==void 0&&(o.alpha=r),o},$a=({x:n,y:e,z:t,alpha:r})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let i=Qs({r:n*3.1341359569958707-e*1.6173863321612538-.4906619460083532*t,g:n*-.978795502912089+e*1.916254567259524+.03344273116131949*t,b:n*.07195537988411677-e*.2289768264158322+1.405386058324125*t});return r!==void 0&&(i.alpha=r),i},Ag=n=>$a(Ef(n)),Ja=n=>{let{r:e,g:t,b:r,alpha:i}=Js(n),s={mode:"xyz50",x:.436065742824811*e+.3851514688337912*t+.14307845442264197*r,y:.22249319175623702*e+.7168870538238823*t+.06061979053616537*r,z:.013923904500943465*e+.09708128566574634*t+.7140993584005155*r};return i!==void 0&&(s.alpha=i),s},hu=n=>n>Tf?Math.cbrt(n):(Vl*n+16)/116,wf=({x:n,y:e,z:t,alpha:r})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let i=hu(n/qt.X),s=hu(e/qt.Y),a=hu(t/qt.Z),o={mode:"lab",l:116*s-16,a:500*(i-s),b:200*(s-a)};return r!==void 0&&(o.alpha=r),o},Rg=n=>{let e=wf(Ja(n));return n.r===n.b&&n.b===n.g&&(e.a=e.b=0),e};function X2(n,e){if(!e||e[0]!=="lab")return;const t={mode:"lab"},[,r,i,s,a]=e;if(!(r.type===Ee.Hue||i.type===Ee.Hue||s.type===Ee.Hue))return r.type!==Ee.None&&(t.l=Math.min(Math.max(0,r.value),100)),i.type!==Ee.None&&(t.a=i.type===Ee.Number?i.value:i.value*125/100),s.type!==Ee.None&&(t.b=s.type===Ee.Number?s.value:s.value*125/100),a.type!==Ee.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ee.Number?a.value:a.value/100))),t}const Af={mode:"lab",toMode:{xyz50:Ef,rgb:Ag},fromMode:{xyz50:wf,rgb:Rg},channels:["l","a","b","alpha"],ranges:{l:[0,100],a:[-125,125],b:[-125,125]},parse:[X2],serialize:n=>`lab(${n.l!==void 0?n.l:"none"} ${n.a!==void 0?n.a:"none"} ${n.b!==void 0?n.b:"none"}${n.alpha<1?` / ${n.alpha}`:""})`,interpolate:{l:Oe,a:Oe,b:Oe,alpha:{use:Oe,fixup:en}}},Y2={...Af,mode:"lab65",parse:["--lab-d65"],serialize:"--lab-d65",toMode:{xyz65:dg,rgb:Ol},fromMode:{xyz65:pg,rgb:Bl},ranges:{l:[0,100],a:[-125,125],b:[-125,125]}};function q2(n,e){if(!e||e[0]!=="lch")return;const t={mode:"lch"},[,r,i,s,a]=e;if(r.type!==Ee.None){if(r.type===Ee.Hue)return;t.l=Math.min(Math.max(0,r.value),100)}if(i.type!==Ee.None&&(t.c=Math.max(0,i.type===Ee.Number?i.value:i.value*150/100)),s.type!==Ee.None){if(s.type===Ee.Percentage)return;t.h=s.value}return a.type!==Ee.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ee.Number?a.value:a.value/100))),t}const Rf={mode:"lch",toMode:{lab:yr,rgb:n=>Ag(yr(n))},fromMode:{rgb:n=>br(Rg(n)),lab:br},channels:["l","c","h","alpha"],ranges:{l:[0,100],c:[0,150],h:[0,360]},parse:[q2],serialize:n=>`lch(${n.l!==void 0?n.l:"none"} ${n.c!==void 0?n.c:"none"} ${n.h!==void 0?n.h:"none"}${n.alpha<1?` / ${n.alpha}`:""})`,interpolate:{h:{use:Oe,fixup:$i},c:Oe,l:Oe,alpha:{use:Oe,fixup:en}},difference:{h:Nl},average:{h:Ji}},j2={...Rf,mode:"lch65",parse:["--lch-d65"],serialize:"--lch-d65",toMode:{lab65:n=>yr(n,"lab65"),rgb:n=>Ol(yr(n,"lab65"))},fromMode:{rgb:n=>br(Bl(n),"lch65"),lab65:n=>br(n,"lch65")},ranges:{l:[0,100],c:[0,150],h:[0,360]}},Cg=({l:n,u:e,v:t,alpha:r})=>{e===void 0&&(e=0),t===void 0&&(t=0);let i=Math.sqrt(e*e+t*t),s={mode:"lchuv",l:n,c:i};return i&&(s.h=hn(Math.atan2(t,e)*180/Math.PI)),r!==void 0&&(s.alpha=r),s},Pg=({l:n,c:e,h:t,alpha:r})=>{t===void 0&&(t=0);let i={mode:"luv",l:n,u:e?e*Math.cos(t/180*Math.PI):0,v:e?e*Math.sin(t/180*Math.PI):0};return r!==void 0&&(i.alpha=r),i},Dg=(n,e,t)=>4*n/(n+15*e+3*t),Ug=(n,e,t)=>9*e/(n+15*e+3*t),K2=Dg(qt.X,qt.Y,qt.Z),Z2=Ug(qt.X,qt.Y,qt.Z),$2=n=>n<=Tf?Vl*n:116*Math.cbrt(n)-16,kh=({x:n,y:e,z:t,alpha:r})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let i=$2(e/qt.Y),s=Dg(n,e,t),a=Ug(n,e,t);!isFinite(s)||!isFinite(a)?i=s=a=0:(s=13*i*(s-K2),a=13*i*(a-Z2));let o={mode:"luv",l:i,u:s,v:a};return r!==void 0&&(o.alpha=r),o},J2=(n,e,t)=>4*n/(n+15*e+3*t),Q2=(n,e,t)=>9*e/(n+15*e+3*t),ew=J2(qt.X,qt.Y,qt.Z),tw=Q2(qt.X,qt.Y,qt.Z),zh=({l:n,u:e,v:t,alpha:r})=>{if(n===void 0&&(n=0),n===0)return{mode:"xyz50",x:0,y:0,z:0};e===void 0&&(e=0),t===void 0&&(t=0);let i=e/(13*n)+ew,s=t/(13*n)+tw,a=qt.Y*(n<=8?n/Vl:Math.pow((n+16)/116,3)),o=a*(9*i)/(4*s),l=a*(12-3*i-20*s)/(4*s),c={mode:"xyz50",x:o,y:a,z:l};return r!==void 0&&(c.alpha=r),c},nw=n=>Cg(kh(Ja(n))),iw=n=>$a(zh(Pg(n))),rw={mode:"lchuv",toMode:{luv:Pg,rgb:iw},fromMode:{rgb:nw,luv:Cg},channels:["l","c","h","alpha"],parse:["--lchuv"],serialize:"--lchuv",ranges:{l:[0,100],c:[0,176.956],h:[0,360]},interpolate:{h:{use:Oe,fixup:$i},c:Oe,l:Oe,alpha:{use:Oe,fixup:en}},difference:{h:Nl},average:{h:Ji}},sw={...$s,mode:"lrgb",toMode:{rgb:Qs},fromMode:{rgb:Js},parse:["srgb-linear"],serialize:"srgb-linear"},aw={mode:"luv",toMode:{xyz50:zh,rgb:n=>$a(zh(n))},fromMode:{xyz50:kh,rgb:n=>kh(Ja(n))},channels:["l","u","v","alpha"],parse:["--luv"],serialize:"--luv",ranges:{l:[0,100],u:[-84.936,175.042],v:[-125.882,87.243]},interpolate:{l:Oe,u:Oe,v:Oe,alpha:{use:Oe,fixup:en}}},Lg=({r:n,g:e,b:t,alpha:r})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let i=Math.cbrt(.412221469470763*n+.5363325372617348*e+.0514459932675022*t),s=Math.cbrt(.2119034958178252*n+.6806995506452344*e+.1073969535369406*t),a=Math.cbrt(.0883024591900564*n+.2817188391361215*e+.6299787016738222*t),o={mode:"oklab",l:.210454268309314*i+.7936177747023054*s-.0040720430116193*a,a:1.9779985324311684*i-2.42859224204858*s+.450593709617411*a,b:.0259040424655478*i+.7827717124575296*s-.8086757549230774*a};return r!==void 0&&(o.alpha=r),o},Wl=n=>{let e=Lg(Js(n));return n.r===n.b&&n.b===n.g&&(e.a=e.b=0),e},Qa=({l:n,a:e,b:t,alpha:r})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let i=Math.pow(n+.3963377773761749*e+.2158037573099136*t,3),s=Math.pow(n-.1055613458156586*e-.0638541728258133*t,3),a=Math.pow(n-.0894841775298119*e-1.2914855480194092*t,3),o={mode:"lrgb",r:4.076741636075957*i-3.3077115392580616*s+.2309699031821044*a,g:-1.2684379732850317*i+2.6097573492876887*s-.3413193760026573*a,b:-.0041960761386756*i-.7034186179359362*s+1.7076146940746117*a};return r!==void 0&&(o.alpha=r),o},Xl=n=>Qs(Qa(n));function Gh(n){const r=1.170873786407767;return .5*(r*n-.206+Math.sqrt((r*n-.206)*(r*n-.206)+4*.03*r*n))}function El(n){return(n*n+.206*n)/(1.170873786407767*(n+.03))}function ow(n,e){let t,r,i,s,a,o,l,c;-1.88170328*n-.80936493*e>1?(t=1.19086277,r=1.76576728,i=.59662641,s=.75515197,a=.56771245,o=4.0767416621,l=-3.3077115913,c=.2309699292):1.81444104*n-1.19445276*e>1?(t=.73956515,r=-.45954404,i=.08285427,s=.1254107,a=.14503204,o=-1.2684380046,l=2.6097574011,c=-.3413193965):(t=1.35733652,r=-.00915799,i=-1.1513021,s=-.50559606,a=.00692167,o=-.0041960863,l=-.7034186147,c=1.707614701);let u=t+r*n+i*e+s*n*n+a*n*e,f=.3963377774*n+.2158037573*e,h=-.1055613458*n-.0638541728*e,d=-.0894841775*n-1.291485548*e;{let m=1+u*f,g=1+u*h,p=1+u*d,_=m*m*m,M=g*g*g,y=p*p*p,v=3*f*m*m,S=3*h*g*g,b=3*d*p*p,E=6*f*f*m,x=6*h*h*g,w=6*d*d*p,R=o*_+l*M+c*y,L=o*v+l*S+c*b,A=o*E+l*x+c*w;u=u-R*L/(L*L-.5*R*A)}return u}function Cf(n,e){let t=ow(n,e),r=Qa({l:1,a:t*n,b:t*e}),i=Math.cbrt(1/Math.max(r.r,r.g,r.b)),s=i*t;return[i,s]}function lw(n,e,t,r,i,s=null){s||(s=Cf(n,e));let a;if((t-i)*s[1]-(s[0]-i)*r<=0)a=s[1]*i/(r*s[0]+s[1]*(i-t));else{a=s[1]*(i-1)/(r*(s[0]-1)+s[1]*(i-t));{let o=t-i,l=r,c=.3963377774*n+.2158037573*e,u=-.1055613458*n-.0638541728*e,f=-.0894841775*n-1.291485548*e,h=o+l*c,d=o+l*u,m=o+l*f;{let g=i*(1-a)+a*t,p=a*r,_=g+p*c,M=g+p*u,y=g+p*f,v=_*_*_,S=M*M*M,b=y*y*y,E=3*h*_*_,x=3*d*M*M,w=3*m*y*y,R=6*h*h*_,L=6*d*d*M,A=6*m*m*y,U=4.0767416621*v-3.3077115913*S+.2309699292*b-1,P=4.0767416621*E-3.3077115913*x+.2309699292*w,I=4.0767416621*R-3.3077115913*L+.2309699292*A,F=P/(P*P-.5*U*I),O=-U*F,q=-1.2684380046*v+2.6097574011*S-.3413193965*b-1,z=-1.2684380046*E+2.6097574011*x-.3413193965*w,k=-1.2684380046*R+2.6097574011*L-.3413193965*A,N=z/(z*z-.5*q*k),G=-q*N,K=-.0041960863*v-.7034186147*S+1.707614701*b-1,J=-.0041960863*E-.7034186147*x+1.707614701*w,j=-.0041960863*R-.7034186147*L+1.707614701*A,V=J/(J*J-.5*K*j),Y=-K*V;O=F>=0?O:1e6,G=N>=0?G:1e6,Y=V>=0?Y:1e6,a+=Math.min(O,Math.min(G,Y))}}}return a}function Pf(n,e,t=null){t||(t=Cf(n,e));let r=t[0],i=t[1];return[i/r,i/(1-r)]}function Ig(n,e,t){let r=Cf(e,t),i=lw(e,t,n,1,n,r),s=Pf(e,t,r),a=.11516993+1/(7.4477897+4.1590124*t+e*(-2.19557347+1.75198401*t+e*(-2.13704948-10.02301043*t+e*(-4.24894561+5.38770819*t+4.69891013*e)))),o=.11239642+1/(1.6132032-.68124379*t+e*(.40370612+.90148123*t+e*(-.27087943+.6122399*t+e*(.00299215-.45399568*t-.14661872*e)))),l=i/Math.min(n*s[0],(1-n)*s[1]),c=n*a,u=(1-n)*o,f=.9*l*Math.sqrt(Math.sqrt(1/(1/(c*c*c*c)+1/(u*u*u*u))));return c=n*.4,u=(1-n)*.8,[Math.sqrt(1/(1/(c*c)+1/(u*u))),f,i]}function jp(n){const e=n.l!==void 0?n.l:0,t=n.a!==void 0?n.a:0,r=n.b!==void 0?n.b:0,i={mode:"okhsl",l:Gh(e)};n.alpha!==void 0&&(i.alpha=n.alpha);let s=Math.sqrt(t*t+r*r);if(!s)return i.s=0,i;let[a,o,l]=Ig(e,t/s,r/s),c;if(s<o){let u=0,f=.8*a,h=1-f/o;c=(s-u)/(f+h*(s-u))*.8}else{let u=o,f=.2*o*o*1.25*1.25/a,h=1-f/(l-o);c=.8+.2*((s-u)/(f+h*(s-u)))}return c&&(i.s=c,i.h=hn(Math.atan2(r,t)*180/Math.PI)),i}function Kp(n){let e=n.h!==void 0?n.h:0,t=n.s!==void 0?n.s:0,r=n.l!==void 0?n.l:0;const i={mode:"oklab",l:El(r)};if(n.alpha!==void 0&&(i.alpha=n.alpha),!t||r===1)return i.a=i.b=0,i;let s=Math.cos(e/180*Math.PI),a=Math.sin(e/180*Math.PI),[o,l,c]=Ig(i.l,s,a),u,f,h,d;t<.8?(u=1.25*t,f=0,h=.8*o,d=1-h/l):(u=5*(t-.8),f=l,h=.2*l*l*1.25*1.25/o,d=1-h/(c-l));let m=f+u*h/(1-d*u);return i.a=m*s,i.b=m*a,i}const cw={..._g,mode:"okhsl",channels:["h","s","l","alpha"],parse:["--okhsl"],serialize:"--okhsl",fromMode:{oklab:jp,rgb:n=>jp(Wl(n))},toMode:{oklab:Kp,rgb:n=>Xl(Kp(n))}};function Zp(n){let e=n.l!==void 0?n.l:0,t=n.a!==void 0?n.a:0,r=n.b!==void 0?n.b:0,i=Math.sqrt(t*t+r*r),s=i?t/i:1,a=i?r/i:1,[o,l]=Pf(s,a),c=.5,u=1-c/o,f=l/(i+e*l),h=f*e,d=f*i,m=El(h),g=d*m/h,p=Qa({l:m,a:s*g,b:a*g}),_=Math.cbrt(1/Math.max(p.r,p.g,p.b,0));e=e/_,i=i/_*Gh(e)/e,e=Gh(e);const M={mode:"okhsv",s:i?(c+l)*d/(l*c+l*u*d):0,v:e?e/h:0};return M.s&&(M.h=hn(Math.atan2(r,t)*180/Math.PI)),n.alpha!==void 0&&(M.alpha=n.alpha),M}function $p(n){const e={mode:"oklab"};n.alpha!==void 0&&(e.alpha=n.alpha);const t=n.h!==void 0?n.h:0,r=n.s!==void 0?n.s:0,i=n.v!==void 0?n.v:0,s=Math.cos(t/180*Math.PI),a=Math.sin(t/180*Math.PI),[o,l]=Pf(s,a),c=.5,u=1-c/o,f=1-r*c/(c+l-l*u*r),h=r*l*c/(c+l-l*u*r),d=El(f),m=h*d/f,g=Qa({l:d,a:s*m,b:a*m}),p=Math.cbrt(1/Math.max(g.r,g.g,g.b,0)),_=El(i*f),M=h*_/f;return e.l=_*p,e.a=M*s*p,e.b=M*a*p,e}const uw={...Mg,mode:"okhsv",channels:["h","s","v","alpha"],parse:["--okhsv"],serialize:"--okhsv",fromMode:{oklab:Zp,rgb:n=>Zp(Wl(n))},toMode:{oklab:$p,rgb:n=>Xl($p(n))}};function hw(n,e){if(!e||e[0]!=="oklab")return;const t={mode:"oklab"},[,r,i,s,a]=e;if(!(r.type===Ee.Hue||i.type===Ee.Hue||s.type===Ee.Hue))return r.type!==Ee.None&&(t.l=Math.min(Math.max(0,r.type===Ee.Number?r.value:r.value/100),1)),i.type!==Ee.None&&(t.a=i.type===Ee.Number?i.value:i.value*.4/100),s.type!==Ee.None&&(t.b=s.type===Ee.Number?s.value:s.value*.4/100),a.type!==Ee.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ee.Number?a.value:a.value/100))),t}const fw={...Af,mode:"oklab",toMode:{lrgb:Qa,rgb:Xl},fromMode:{lrgb:Lg,rgb:Wl},ranges:{l:[0,1],a:[-.4,.4],b:[-.4,.4]},parse:[hw],serialize:n=>`oklab(${n.l!==void 0?n.l:"none"} ${n.a!==void 0?n.a:"none"} ${n.b!==void 0?n.b:"none"}${n.alpha<1?` / ${n.alpha}`:""})`};function dw(n,e){if(!e||e[0]!=="oklch")return;const t={mode:"oklch"},[,r,i,s,a]=e;if(r.type!==Ee.None){if(r.type===Ee.Hue)return;t.l=Math.min(Math.max(0,r.type===Ee.Number?r.value:r.value/100),1)}if(i.type!==Ee.None&&(t.c=Math.max(0,i.type===Ee.Number?i.value:i.value*.4/100)),s.type!==Ee.None){if(s.type===Ee.Percentage)return;t.h=s.value}return a.type!==Ee.None&&(t.alpha=Math.min(1,Math.max(0,a.type===Ee.Number?a.value:a.value/100))),t}const pw={...Rf,mode:"oklch",toMode:{oklab:n=>yr(n,"oklab"),rgb:n=>Xl(yr(n,"oklab"))},fromMode:{rgb:n=>br(Wl(n),"oklch"),oklab:n=>br(n,"oklch")},parse:[dw],serialize:n=>`oklch(${n.l!==void 0?n.l:"none"} ${n.c!==void 0?n.c:"none"} ${n.h!==void 0?n.h:"none"}${n.alpha<1?` / ${n.alpha}`:""})`,ranges:{l:[0,1],c:[0,.4],h:[0,360]}},Jp=n=>{let{r:e,g:t,b:r,alpha:i}=Js(n),s={mode:"xyz65",x:.486570948648216*e+.265667693169093*t+.1982172852343625*r,y:.2289745640697487*e+.6917385218365062*t+.079286914093745*r,z:0*e+.0451133818589026*t+1.043944368900976*r};return i!==void 0&&(s.alpha=i),s},Qp=({x:n,y:e,z:t,alpha:r})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let i=Qs({r:n*2.4934969119414263-e*.9313836179191242-.402710784450717*t,g:n*-.8294889695615749+e*1.7626640603183465+.0236246858419436*t,b:n*.0358458302437845-e*.0761723892680418+.9568845240076871*t},"p3");return r!==void 0&&(i.alpha=r),i},mw={...$s,mode:"p3",parse:["display-p3"],serialize:"display-p3",fromMode:{rgb:n=>Qp(Qr(n)),xyz65:Qp},toMode:{rgb:n=>es(Jp(n)),xyz65:Jp}},fu=n=>{let e=Math.abs(n);return e>=1/512?Math.sign(n)*Math.pow(e,1/1.8):16*n},em=({x:n,y:e,z:t,alpha:r})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let i={mode:"prophoto",r:fu(n*1.3457868816471585-e*.2555720873797946-.0511018649755453*t),g:fu(n*-.5446307051249019+e*1.5082477428451466+.0205274474364214*t),b:fu(n*0+e*0+1.2119675456389452*t)};return r!==void 0&&(i.alpha=r),i},du=(n=0)=>{let e=Math.abs(n);return e>=16/512?Math.sign(n)*Math.pow(e,1.8):n/16},tm=n=>{let e=du(n.r),t=du(n.g),r=du(n.b),i={mode:"xyz50",x:.7977666449006423*e+.1351812974005331*t+.0313477341283922*r,y:.2880748288194013*e+.7118352342418731*t+899369387256e-16*r,z:0*e+0*t+.8251046025104602*r};return n.alpha!==void 0&&(i.alpha=n.alpha),i},gw={...$s,mode:"prophoto",parse:["prophoto-rgb"],serialize:"prophoto-rgb",fromMode:{xyz50:em,rgb:n=>em(Ja(n))},toMode:{xyz50:tm,rgb:n=>$a(tm(n))}},nm=1.09929682680944,_w=.018053968510807,pu=n=>{const e=Math.abs(n);return e>_w?(Math.sign(n)||1)*(nm*Math.pow(e,.45)-(nm-1)):4.5*n},im=({x:n,y:e,z:t,alpha:r})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);let i={mode:"rec2020",r:pu(n*1.7166511879712683-e*.3556707837763925-.2533662813736599*t),g:pu(n*-.6666843518324893+e*1.6164812366349395+.0157685458139111*t),b:pu(n*.0176398574453108-e*.0427706132578085+.9421031212354739*t)};return r!==void 0&&(i.alpha=r),i},rm=1.09929682680944,vw=.018053968510807,mu=(n=0)=>{let e=Math.abs(n);return e<vw*4.5?n/4.5:(Math.sign(n)||1)*Math.pow((e+rm-1)/rm,1/.45)},sm=n=>{let e=mu(n.r),t=mu(n.g),r=mu(n.b),i={mode:"xyz65",x:.6369580483012911*e+.1446169035862083*t+.1688809751641721*r,y:.262700212011267*e+.6779980715188708*t+.059301716469862*r,z:0*e+.0280726930490874*t+1.0609850577107909*r};return n.alpha!==void 0&&(i.alpha=n.alpha),i},xw={...$s,mode:"rec2020",fromMode:{xyz65:im,rgb:n=>im(Qr(n))},toMode:{xyz65:sm,rgb:n=>es(sm(n))},parse:["rec2020"],serialize:"rec2020"},qr=.0037930732552754493,Fg=Math.cbrt(qr),gu=n=>Math.cbrt(n)-Fg,Mw=n=>{const{r:e,g:t,b:r,alpha:i}=Js(n),s=gu(.3*e+.622*t+.078*r+qr),a=gu(.23*e+.692*t+.078*r+qr),o=gu(.2434226892454782*e+.2047674442449682*t+.5518098665095535*r+qr),l={mode:"xyb",x:(s-a)/2,y:(s+a)/2,b:o-(s+a)/2};return i!==void 0&&(l.alpha=i),l},_u=n=>Math.pow(n+Fg,3),Sw=({x:n,y:e,b:t,alpha:r})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);const i=_u(n+e)-qr,s=_u(e-n)-qr,a=_u(t+e)-qr,o=Qs({r:11.031566904639861*i-9.866943908131562*s-.16462299650829934*a,g:-3.2541473810744237*i+4.418770377582723*s-.16462299650829934*a,b:-3.6588512867136815*i+2.7129230459360922*s+1.9459282407775895*a});return r!==void 0&&(o.alpha=r),o},bw={mode:"xyb",channels:["x","y","b","alpha"],parse:["--xyb"],serialize:"--xyb",toMode:{rgb:Sw},fromMode:{rgb:Mw},ranges:{x:[-.0154,.0281],y:[0,.8453],b:[-.2778,.388]},interpolate:{x:Oe,y:Oe,b:Oe,alpha:{use:Oe,fixup:en}}},yw={mode:"xyz50",parse:["xyz-d50"],serialize:"xyz-d50",toMode:{rgb:$a,lab:wf},fromMode:{rgb:Ja,lab:Ef},channels:["x","y","z","alpha"],ranges:{x:[0,.964],y:[0,.999],z:[0,.825]},interpolate:{x:Oe,y:Oe,z:Oe,alpha:{use:Oe,fixup:en}}},Tw=n=>{let{x:e,y:t,z:r,alpha:i}=n;e===void 0&&(e=0),t===void 0&&(t=0),r===void 0&&(r=0);let s={mode:"xyz50",x:1.0479298208405488*e+.0229467933410191*t-.0501922295431356*r,y:.0296278156881593*e+.990434484573249*t-.0170738250293851*r,z:-.0092430581525912*e+.0150551448965779*t+.7518742899580008*r};return i!==void 0&&(s.alpha=i),s},Ew=n=>{let{x:e,y:t,z:r,alpha:i}=n;e===void 0&&(e=0),t===void 0&&(t=0),r===void 0&&(r=0);let s={mode:"xyz65",x:.9554734527042182*e-.0230985368742614*t+.0632593086610217*r,y:-.0283697069632081*e+1.0099954580058226*t+.021041398966943*r,z:.0123140016883199*e-.0205076964334779*t+1.3303659366080753*r};return i!==void 0&&(s.alpha=i),s},ww={mode:"xyz65",toMode:{rgb:es,xyz50:Tw},fromMode:{rgb:Qr,xyz50:Ew},ranges:{x:[0,.95],y:[0,1],z:[0,1.088]},channels:["x","y","z","alpha"],parse:["xyz","xyz-d65"],serialize:"xyz-d65",interpolate:{x:Oe,y:Oe,z:Oe,alpha:{use:Oe,fixup:en}}},Aw=({r:n,g:e,b:t,alpha:r})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);const i={mode:"yiq",y:.29889531*n+.58662247*e+.11448223*t,i:.59597799*n-.2741761*e-.32180189*t,q:.21147017*n-.52261711*e+.31114694*t};return r!==void 0&&(i.alpha=r),i},Rw=({y:n,i:e,q:t,alpha:r})=>{n===void 0&&(n=0),e===void 0&&(e=0),t===void 0&&(t=0);const i={mode:"rgb",r:n+.95608445*e+.6208885*t,g:n-.27137664*e-.6486059*t,b:n-1.10561724*e+1.70250126*t};return r!==void 0&&(i.alpha=r),i},Cw={mode:"yiq",toMode:{rgb:Rw},fromMode:{rgb:Aw},channels:["y","i","q","alpha"],parse:["--yiq"],serialize:"--yiq",ranges:{i:[-.595,.595],q:[-.522,.522]},interpolate:{y:Oe,i:Oe,q:Oe,alpha:{use:Oe,fixup:en}}},Pw=n=>{n[0]===void 0&&(n[0]=0),n[n.length-1]===void 0&&(n[n.length-1]=1);let e=1,t,r,i,s;for(;e<n.length;){if(n[e]===void 0){for(r=e,i=n[e-1],t=e;n[t]===void 0;)t++;for(s=(n[t]-i)/(t-e+1);e<t;)n[e]=i+(e+1-r)*s,e++}else n[e]<n[e-1]&&(n[e]=n[e-1]);e++}return n},Dw=(n=.5)=>e=>n<=0?1:n>=1?0:Math.pow(e,Math.log(.5)/Math.log(n)),Go=n=>typeof n=="function",Ir=n=>n&&typeof n=="object",am=n=>typeof n=="number",Uw=(n,e="rgb",t,r)=>{let i=cg(e),s=yf(e),a=[],o=[],l={};n.forEach(h=>{Array.isArray(h)?(a.push(s(h[0])),o.push(h[1])):am(h)||Go(h)?l[o.length]=h:(a.push(s(h)),o.push(void 0))}),Pw(o);let c=i.channels.reduce((h,d)=>{let m;return Ir(t)&&Ir(t[d])&&t[d].fixup?m=t[d].fixup:Ir(i.interpolate[d])&&i.interpolate[d].fixup?m=i.interpolate[d].fixup:m=g=>g,h[d]=m(a.map(g=>g[d])),h},{}),u=i.channels.reduce((h,d)=>{let m;return Go(t)?m=t:Ir(t)&&Go(t[d])?m=t[d]:Ir(t)&&Ir(t[d])&&t[d].use?m=t[d].use:Go(i.interpolate[d])?m=i.interpolate[d]:Ir(i.interpolate[d])&&(m=i.interpolate[d].use),h[d]=m(c[d]),h},{}),f=a.length-1;return h=>{if(h=Math.min(Math.max(0,h),1),h<=o[0])return a[0];if(h>o[f])return a[f];let d=0;for(;o[d]<h;)d++;let m=o[d-1],g=o[d]-m,p=(h-m)/g,_=l[d]||l[0];_!==void 0&&(am(_)&&(_=Dw((_-m)/g)),p=_(p));let M=(d-1+p)/f;return i.channels.reduce((y,v)=>{let S=u[v](M);return S!==void 0&&(y[v]=S),y},{mode:e})}},Lw=(n,e="rgb",t)=>Uw(n,e,t);vt(g2);vt(y2);vt(T2);vt(E2);vt(R2);vt(_g);vt(Mg);vt(B2);vt(k2);vt(V2);vt(W2);vt(Af);vt(Y2);vt(Rf);vt(j2);vt(rw);vt(sw);vt(aw);vt(cw);vt(uw);vt(fw);vt(pw);vt(mw);vt(gw);vt(xw);vt($s);vt(bw);vt(yw);vt(ww);vt(Cw);function Mi(n){let e=n>>>0;return()=>{e|=0,e=e+1831565813|0;let t=Math.imul(e^e>>>15,1|e);return t=t+Math.imul(t^t>>>7,61|t)^t,((t^t>>>14)>>>0)/4294967296}}const At=100,Df=At/400,Ca=.3*At,Na=.54*At,Iw=.95*At,vu=At+22*Df,Ho=At+52*Df,xu=At+37*Df,Fw=-160,En=15262418,Nw=14462549,Ow=15781247,ws=[-145,-72,-2,52,160],om=[{slots:[[0,4,1.15],[-.5,-1.5,.68],[-4,-6,.62],[-8,-8.5,.78],[-11.2,-7.2,.58],[3,-5.5,.62],[6.8,-7.8,.72]],links:[[0,1],[1,2],[2,3],[3,4],[1,5],[5,6]]},{slots:[[-11.8,2.8,.62],[-6,.5,.72],[-.5,-1,.92],[5,-.5,.68],[10.8,1.8,.6]],links:[[0,1],[1,2],[2,3],[3,4]]},{slots:[[-8.8,-1.8,.62],[-4.5,2,.7],[0,3.5,.9],[4.5,2,.7],[8.8,-1.8,.62]],links:[[0,1],[1,2],[2,3],[3,4]]},{slots:[[-2,-1.2,.85],[2.2,-.8,.65],[0,2,.6]],links:[[0,1],[1,2],[2,0]]},{slots:[[-9.2,-2.5,.62],[-4,2.2,.72],[1,-2.2,.82],[6,2.5,.65],[10.2,-.8,.6]],links:[[0,1],[1,2],[2,3],[3,4]]}],Bw=[[-40,18,.72,1],[-78,11.5,.6,0],[-112,15.5,.68,0],[-148,12.5,.58,0],[168,19,.78,1],[142,11.5,.58,0],[116,17,.65,0],[88,11,.58,0],[58,15,.72,1],[34,21,.6,0],[-32,24,.62,0],[-95,22.5,.65,1]],kw=[[0,1],[1,2],[2,3],[5,6],[6,7],[8,9]];function xi(n,e){const t=e*Math.PI/180;return[n*Math.cos(t),n*Math.sin(t)]}function zw(n){return n=n%360,n>180&&(n-=360),n<-180&&(n+=360),n}function Gw(n){const e=Mi(20260921),t=n.categories.reduce((A,U)=>A+U.count,0)||1,r=[];let i=Fw;for(const A of n.categories){const U=A.count/t*360;r.push({id:A.id,name:A.name,start:i,width:U,count:A.count}),i+=U}const s=A=>r.find(U=>U.id===A),a=[.961,.918,.824],o={plan:[],deep:[],size:[],opacity:[],core:[],ring:[],legacyRing:[],color:[],filler:[],deepOpScale:[],deepSizeScale:[]},l=(A,U,P,I,F,O,q,z,k,N,G,K,J,j)=>{o.plan.push(A,U,0),o.deep.push(P,I,F),o.size.push(O),o.opacity.push(q),o.core.push(K),o.ring.push(J),o.legacyRing.push(j),o.color.push(k[0],k[1],k[2]),o.filler.push(z?1:0),o.deepOpScale.push(N),o.deepSizeScale.push(G)},c=()=>[(e()*2-1)*250,(e()*2-1)*140,40-e()*180],u=new Map;for(const A of n.skills)u.has(A.category)||u.set(A.category,[]),u.get(A.category).push(A);for(const A of n.skills){if(A.lit||A.status==="learning")continue;const U=s(A.category);if(!U)continue;const P=U.start+1.5+e()*(U.width-3),I=At*(.34+.58*Math.sqrt(e())),[F,O]=xi(I,P),[q,z,k]=c();l(F,O,q,z,k,.62+e()*.2,.34+e()*.08,!1,a,.6,.55,0,1,e()<.3?1:0)}const f=1800;for(const A of r){const U=Math.round(A.count/t*f);for(let P=0;P<U;P++){let I,F;if(e()<.15){if(I=e()*360,F=Ca*(.52+.46*e()),Math.abs(zw(I))<25)continue}else I=A.start+1.3+e()*(A.width-2.6),F=At*(.33+.61*Math.sqrt(e()));const[O,q]=xi(F,I),[z,k,N]=c(),G=[1,.88,.69],K=[.74,.81,1],J=e(),j=J>.975?G:J>.95?K:a,V=J>.992,Y=V?1.1:.15+Math.pow(e(),1.8)*.85,Z=V?.9:.35+Math.pow(e(),2)*.5;l(O,q,z,k,N,V?.62:.34+e()*.22,V?.38:.1+e()*.12,!0,j,Y,Z,1,0,e()<.18?1:0)}}const h={plan:[],deep:[],size:[],opacity:[],core:[],ring:[],color:[],links:[],skills:[]},d=new Map;n.evidence.forEach(A=>A.skill_ids.forEach(U=>d.set(U,(d.get(U)||0)+1)));let m=0;n.categories.forEach((A,U)=>{const P=(u.get(A.id)||[]).filter(K=>K.lit||K.status==="learning");if(!P.length)return;const I=s(A.id);if(!I)return;const F=I.start+I.width/2,[O,q]=xi(At*.72,F),z=om[U%om.length],k=Mi(500+U),N=z.slots.slice(0,P.length);for(;N.length<P.length;){const K=N[N.length-1];N.push([K[0]+4.5,K[1]+(k()-.5)*3,.58])}const G=m;if(P.forEach((K,J)=>{const[j,V,Y]=N[J],Z=O+(j+(k()-.5)*1.6),fe=q+(V+(k()-.5)*1.6),[_e,le,de]=c();h.plan.push(Z,fe,0),h.deep.push(_e,le,de),h.size.push(Y*(K.lit?1.15:.9)),h.opacity.push(K.lit?.95:.55),h.core.push(1),h.ring.push(K.lit?1:0),h.color.push(.961,.918,.824),h.skills.push({id:K.id,label:K.label,category:K.category,status:K.status,evidenceCount:d.get(K.id)||0}),m+=1}),P.length>=3)for(const[K,J]of z.links)K<P.length&&J<P.length&&h.links.push(G+K,G+J)});const g=n.goals.slice(0,5).map((A,U)=>{const[P,I]=xi(Na,ws[U%ws.length]),F=Mi(900+U);return{title:A.title,angle:ws[U%ws.length],plan:[P,I,0],deep:[P+(F()-.5)*10,I+(F()-.5)*6,(F()-.5)*24]}}),p={plan:[],size:[],gold:[],links:kw};for(const[A,U,P,I]of Bw){const[F,O]=xi(U,A);p.plan.push(F,O,0),p.size.push(P),p.gold.push(I)}const _=new Map(n.skills.map(A=>[A.id,A.category])),M=new Map(n.goals.slice(0,5).map((A,U)=>[A.id,ws[U%ws.length]])),y=[-13,9,-6,15],v=new Map;let S=0;const b=[];n.projects.forEach(A=>{const U=(A.goal_ids||[]).find(k=>M.has(k));let P,I,F=-1;if(U!==void 0){F=n.goals.findIndex(N=>N.id===U);const k=v.get(U)||0;v.set(U,k+1),P=M.get(U)+y[k%y.length],I=Na+(k%2===0?-10:10)}else P=-170+S*42,S+=1,I=Na+24;const[O,q]=xi(I,P),z=Mi(3e3+b.length);b.push({id:A.id,title:A.title,status:A.status,progress:A.progress,taskCount:A.task_count,goalIndex:F,plan:[O,q,0],deep:[O+(z()-.5)*8,q+(z()-.5)*8,(z()-.5)*10]})});const E={plan:[],deep:[],size:[],opacity:[]};b.forEach((A,U)=>{const P=Mi(3100+U);for(let I=0;I<Math.min(A.taskCount,5);I++){const F=P()*360,O=3.8+P()*2.4,[q,z]=xi(O,F);E.plan.push(A.plan[0]+q,A.plan[1]+z,0),E.deep.push(A.deep[0]+q*1.3,A.deep[1]+z*1.3,A.deep[2]+(P()-.5)*4),E.size.push(.42),E.opacity.push(A.status==="active"?.55:.3)}});const x={weak:4,unrated:4,medium:6.5,strong:9,high_trust:12},w=[];n.evidence.filter(A=>A.flying).forEach((A,U)=>{const P=Mi(3200+U),I=P()*360,F=At*(.42+.42*P()),[O,q]=xi(F,I);w.push({id:A.id,title:A.title,date:A.date,strength:A.strength,review:A.review_status,plan:[O,q,0],deep:[(P()*2-1)*230,(P()*2-1)*120,30-P()*150],tailDir:I+90+(P()-.5)*30,tailLen:x[A.strength]||5})});const R={plan:[],deep:[],size:[],opacity:[]};n.evidence.filter(A=>!A.flying).forEach((A,U)=>{const P=Mi(3300+U);let I,F;const O=A.project_refs.length&&b.find(q=>q.id===A.project_refs[0]);if(O){const[q,z]=xi(5.5+P()*4,P()*360);I=O.plan[0]+q,F=O.plan[1]+z}else{const q=A.skill_ids.length?_.get(A.skill_ids[0]):void 0,z=q&&s(q)||r[Math.floor(P()*r.length)];if(!z)return;const k=z.start+2+P()*(z.width-4),N=At*(.45+.43*Math.sqrt(P()));[I,F]=xi(N,k)}R.plan.push(I,F,0),R.deep.push((P()*2-1)*240,(P()*2-1)*130,40-P()*170),R.size.push(.5),R.opacity.push(.4)});const L={plan:[],deep:[],size:[],opacity:[],trailPlan:[],trailDeep:[]};{const A=[-1.15*At,-.35*At],U=[-.42*At,.28*At],P=[.42*At,-.58*At],I=[1.15*At,.04*At],F=n.evidence.length;n.evidence.forEach((O,q)=>{const z=Mi(3400+q),k=F<=1?0:q/(F-1),N=1-k,G=N*N*N*A[0]+3*N*N*k*U[0]+3*N*k*k*P[0]+k*k*k*I[0],K=N*N*N*A[1]+3*N*N*k*U[1]+3*N*k*k*P[1]+k*k*k*I[1];let J=3*N*N*(U[0]-A[0])+6*N*k*(P[0]-U[0])+3*k*k*(I[0]-P[0]),j=3*N*N*(U[1]-A[1])+6*N*k*(P[1]-U[1])+3*k*k*(I[1]-P[1]);const V=Math.hypot(J,j)||1;J/=V,j/=V;const Y=G+(z()-.5)*10,Z=K+(z()-.5)*10,fe=G*1.9+(z()-.5)*20,_e=K*1.9+(z()-.5)*16,le=30-k*130+(z()-.5)*20;L.plan.push(Y,Z,0),L.deep.push(fe,_e,le),L.trailPlan.push(Y,Z,0,Y-J*2.6,Z-j*2.6,0),L.trailDeep.push(fe,_e,le,fe-J*4.9,_e-j*4.9,le-2.2),L.size.push(.75),L.opacity.push(O.review_status==="needs_review"?.38:.2)})}return{sectors:r,dim:o,lit:h,goals:g,court:p,planets:b,moons:E,guests:w,seated:R,dust:L}}const Hw="/assets/NotoSerifSC-subset-Cx3VUXg0.ttf",lm="/assets/IMing-subset-Kpo8eYZB.ttf",cm="/assets/LXGWWenKai-subset-D9yc30St.ttf",Vw="/assets/IMFellEnglish-subset-DL3qchp1.ttf",Mu=(n,e)=>Math.min(1,Math.max(0,(n-e)/.4));class Ww{constructor(e,t,r,i={}){Ie(this,"root");Ie(this,"heart");Ie(this,"snapshot");Ie(this,"opts");Ie(this,"L");Ie(this,"renderer");Ie(this,"composer");Ie(this,"bloom");Ie(this,"fxPass");Ie(this,"scene",new uh);Ie(this,"camera");Ie(this,"chart",new Ta);Ie(this,"canvas");Ie(this,"bgStone");Ie(this,"bgDeep");Ie(this,"bgDusk");Ie(this,"vignette");Ie(this,"tooltip");Ie(this,"fadeMats",[]);Ie(this,"labelObjs",[]);Ie(this,"morphables",[]);Ie(this,"dimPts");Ie(this,"litPts");Ie(this,"goalPts");Ie(this,"planetPts");Ie(this,"guestPts");Ie(this,"planetInnerPts");Ie(this,"moonPts");Ie(this,"guestTails");Ie(this,"glows",[]);Ie(this,"guestGlows",[]);Ie(this,"nebulae",[]);Ie(this,"goalLabelGroups",[]);Ie(this,"selRing");Ie(this,"controls",null);Ie(this,"state",{t:0,density:1,bloom:1,w1:0,w2:.3,w3:.6,duskPos:.45,duskAmt:1,ch1:0,ch2:0,ch3:0});Ie(this,"tween",null);Ie(this,"hoverIdx",-1);Ie(this,"selectedIdx",-1);Ie(this,"hoverables",[]);Ie(this,"clickables",[]);Ie(this,"dragging",!1);Ie(this,"dragLastX",0);Ie(this,"dragLastT",0);Ie(this,"dragDist",0);Ie(this,"spinVel",0);Ie(this,"spinFactor",1);Ie(this,"lastPointerActive",-1e9);Ie(this,"clock",new ov);Ie(this,"rafId",0);Ie(this,"disposed",!1);Ie(this,"resizeObserver",null);Ie(this,"labelsPending",0);Ie(this,"segPending",0);Ie(this,"reducedMotion");Ie(this,"coarsePointer");Ie(this,"softGL");Ie(this,"camPlan",{pos:new X(0,4,346),look:new X(0,0,0)});Ie(this,"camDeep",{pos:new X(0,72,232),look:new X(0,-4,0)});Ie(this,"goalPeriods");Ie(this,"planetPeriods");Ie(this,"guestPeriods");Ie(this,"goalPhase");Ie(this,"planetPhase");Ie(this,"guestPhase");Ie(this,"goalDeepBase");Ie(this,"planetDeepBase");Ie(this,"guestDeepBase");Ie(this,"moonDeepBase");Ie(this,"moonPlanet",[]);Ie(this,"tailOffsets",[]);Ie(this,"guestBaseOpacity");Ie(this,"onPointerMoveWindow",e=>this.onPointerMove(e));Ie(this,"onPointerActive",()=>{this.lastPointerActive=performance.now()});Ie(this,"onClickWindow",e=>this.onClick(e));Ie(this,"onKeydown",e=>{e.key==="Escape"&&this.closeDetail()});Ie(this,"onWheel",(()=>{let e=0;return t=>{e+=t.deltaY,Math.abs(e)>260&&(this.goTo(e<0?1:0),e=0)}})());this.root=e,this.heart=t,this.snapshot=r,this.opts=i,this.L=Gw(r),this.reducedMotion=matchMedia("(prefers-reduced-motion: reduce)").matches,this.coarsePointer=matchMedia("(pointer: coarse)").matches,this.state.t=i.initialState==="deepspace"?1:0;const s=v=>{const S=document.createElement("div");return S.className=v,this.root.appendChild(S),S};this.bgStone=s("starmap-bg"),this.bgDusk=s("starmap-bg"),this.bgDeep=s("starmap-bg"),this.vignette=s("starmap-vignette"),this.canvas=document.createElement("canvas"),this.canvas.className="starmap-canvas",this.heart.appendChild(this.canvas),this.tooltip=s("starmap-tooltip"),this.tooltip.style.display="none",this.renderer=new rb({canvas:this.canvas,antialias:!0,alpha:!0}),this.renderer.setClearColor(0,0),this.renderer.setPixelRatio(Math.min(window.devicePixelRatio,2)),this.camera=new kn(45,1,1,2e3),this.fitPlanCamera(),this.scene.add(this.chart),this.bakeBackgrounds(),this.buildLinework(),this.dimPts=this.makePoints({plan:this.L.dim.plan,deep:this.L.dim.deep,size:this.L.dim.size,opacity:this.L.dim.opacity,core:this.L.dim.core,ring:this.L.dim.ring,color:this.L.dim.color}),this.dimPts.userData.filler=this.L.dim.filler,this.dimPts.userData.baseOpacity=new Float32Array(this.L.dim.opacity),this.dimPts.userData.baseSize=new Float32Array(this.L.dim.size),this.dimPts.userData.baseRing=new Float32Array(this.dimPts.geometry.attributes.aRing.array),this.dimPts.userData.deepOpScale=new Float32Array(this.L.dim.deepOpScale),this.dimPts.userData.deepSizeScale=new Float32Array(this.L.dim.deepSizeScale),this.litPts=this.makePoints({plan:this.L.lit.plan,deep:this.L.lit.deep,size:this.L.lit.size,opacity:this.L.lit.opacity,core:this.L.lit.core,ring:this.L.lit.ring,color:this.L.lit.color}),this.goalPts=this.makePoints({plan:this.L.goals.flatMap(v=>v.plan),deep:this.L.goals.flatMap(v=>v.deep),size:this.L.goals.map(()=>2.6),opacity:this.L.goals.map(()=>1),core:this.L.goals.map(()=>1),ring:this.L.goals.map(()=>1),color:this.L.goals.flatMap(()=>[.91,.72,.36])});const a=this.makePoints({plan:this.L.court.plan,deep:this.L.court.plan.map((v,S)=>S%3===2?v||0:v*1.6),size:this.L.court.size,opacity:this.L.court.gold.map(v=>v?1:.85),core:this.L.court.gold.map(()=>1),ring:this.L.court.gold.map(()=>0),color:this.L.court.gold.flatMap(v=>v?[.91,.72,.36]:[.961,.918,.824])}),o=this.makePoints({plan:[0,0,0],deep:[0,0,0],size:[4.4],opacity:[1],core:[1],ring:[0],color:[.98,.85,.55]});this.planetPts=this.makePoints({plan:this.L.planets.flatMap(v=>v.plan),deep:this.L.planets.flatMap(v=>v.deep),size:this.L.planets.map(()=>3),opacity:this.L.planets.map(v=>v.status==="active"?.9:.35),core:this.L.planets.map(()=>.4),ring:this.L.planets.map(()=>1),color:this.L.planets.flatMap(()=>[.961,.918,.824])}),this.moonPts=this.makePoints({plan:this.L.moons.plan,deep:this.L.moons.deep,size:this.L.moons.size,opacity:this.L.moons.opacity,core:this.L.moons.size.map(()=>1),ring:this.L.moons.size.map(()=>0),color:this.L.moons.size.flatMap(()=>[.961,.918,.824])});const l=this.makePoints({plan:this.L.seated.plan,deep:this.L.seated.deep,size:this.L.seated.size,opacity:this.L.seated.opacity,core:this.L.seated.size.map(()=>1),ring:this.L.seated.size.map(()=>0),color:this.L.seated.size.flatMap(()=>[.961,.918,.824])});this.guestPts=this.makePoints({plan:this.L.guests.flatMap(v=>v.plan),deep:this.L.guests.flatMap(v=>v.deep),size:this.L.guests.map(()=>1.15),opacity:this.L.guests.map(()=>.95),core:this.L.guests.map(()=>1),ring:this.L.guests.map(()=>0),color:this.L.guests.flatMap(()=>[1,.95,.85])});const c=this.makePoints({plan:this.L.dust.plan,deep:this.L.dust.deep,size:this.L.dust.size,opacity:this.L.dust.opacity,core:this.L.dust.size.map(()=>1),ring:this.L.dust.size.map(()=>0),color:this.L.dust.size.flatMap(()=>[.961,.918,.824])}),u=(()=>{const v=new Dt;v.setAttribute("position",new kt(new Float32Array(this.L.dust.trailPlan),3));const S=new Pr(v,this.lineMat(En,.26,.22,3));this.chart.add(S);const b=S;return b.userData.plan=new Float32Array(this.L.dust.trailPlan),b.userData.deep=new Float32Array(this.L.dust.trailDeep),b})();this.planetInnerPts=this.makePoints({plan:this.L.planets.flatMap(v=>v.plan),deep:this.L.planets.flatMap(v=>v.deep),size:this.L.planets.map(()=>2),opacity:this.L.planets.map(v=>v.status==="active"?.9:.35),core:this.L.planets.map(()=>0),ring:this.L.planets.map(()=>1),color:this.L.planets.flatMap(()=>[.961,.918,.824])});{const v=[];for(const S of this.L.planets){if(S.goalIndex<0)continue;const b=this.L.goals[S.goalIndex];v.push(new X(S.plan[0],S.plan[1],0)),v.push(new X(b.plan[0],b.plan[1],0))}this.chart.add(new Pr(new Dt().setFromPoints(v),this.lineMat(En,.22,0,1)))}{const v=[];for(const S of this.L.planets){if(S.progress===null||S.progress===void 0||S.progress<=0)continue;const b=32,E=4.6;for(let x=0;x<b;x++){const w=Math.PI/2-x/b*S.progress*Math.PI*2,R=Math.PI/2-(x+1)/b*S.progress*Math.PI*2;v.push(new X(S.plan[0]+E*Math.cos(w),S.plan[1]+E*Math.sin(w),0)),v.push(new X(S.plan[0]+E*Math.cos(R),S.plan[1]+E*Math.sin(R),0))}}v.length&&this.chart.add(new Pr(new Dt().setFromPoints(v),this.lineMat(Nw,.55,0,2)))}this.guestTails=(()=>{const v=[],S=[];for(const x of this.L.guests){const w=x.tailDir*Math.PI/180,R=Math.cos(w),L=Math.sin(w),A=-L,U=R,P=5;for(let I=0;I<P;I++)for(const F of[I/P,(I+1)/P]){const O=Math.sin(F*2.5)*1.1;v.push(x.plan[0]-R*x.tailLen*F+A*O,x.plan[1]-L*x.tailLen*F+U*O,0),S.push(x.deep[0]-R*x.tailLen*1.3*F+A*O,x.deep[1]-L*x.tailLen*1.3*F+U*O,x.deep[2])}}const b=new Dt;b.setAttribute("position",new kt(new Float32Array(v),3));const E=new Pr(b,this.lineMat(En,.55,.4,3));return this.chart.add(E),E})();{const v=this.guestTails;v.userData.plan=new Float32Array(v.geometry.attributes.position.array),v.userData.deep=new Float32Array(this.L.guests.flatMap(S=>{const b=S.tailDir*Math.PI/180,E=Math.cos(b),x=Math.sin(b),w=-x,R=E,L=[],A=5;for(let U=0;U<A;U++)for(const P of[U/A,(U+1)/A]){const I=Math.sin(P*2.5)*1.1;L.push(S.deep[0]-E*S.tailLen*1.3*P+w*I,S.deep[1]-x*S.tailLen*1.3*P+R*I,S.deep[2])}return L}))}const f=this.makeGlowTexture(),h=(v,S,b,E)=>{const x=new Ko({map:f,color:b,transparent:!0,opacity:0,blending:nl,depthWrite:!1}),w=new yc(x);return w.scale.set(S,S,1),this.chart.add(w),this.glows.push({spr:w,mat:x,getPos:v,maxOpacity:E}),w};h(()=>[0,0,0],20,16767370,.8),h(()=>[0,0,0],40,9873628,.1),this.L.goals.forEach((v,S)=>h(()=>{const b=this.goalPts.geometry.attributes.position.array;return[b[S*3],b[S*3+1],b[S*3+2]]},9,16764280,.35)),this.guestGlows=this.L.guests.map((v,S)=>{const b=new Ko({map:f,color:16771264,transparent:!0,opacity:0,blending:nl,depthWrite:!1}),E=new yc(b);return E.scale.set(5.5,5.5,1),this.chart.add(E),{spr:E,mat:b,idx:S,breathe:v.review==="needs_review"}});for(const[v,S,b,E,x,w]of[[150,70,-120,260,8017464,.13],[-170,-60,-100,300,6119536,.1],[0,120,-140,200,4608634,.085]]){const R=new Ko({map:f,color:x,transparent:!0,opacity:0,depthWrite:!1}),L=new yc(R);L.position.set(v,S,b),L.scale.set(E,E,1),L.visible=!1,this.scene.add(L),this.nebulae.push({mat:R,op:w,spr:L})}this.buildLabels();const d=this.renderer.getContext(),m=d.getExtension("WEBGL_debug_renderer_info"),g=m?String(d.getParameter(m.UNMASKED_RENDERER_WEBGL)):"";this.softGL=/swiftshader|llvmpipe|software/i.test(g),this.composer=new GT(this.renderer),this.composer.addPass(new GE(this.scene,this.camera)),this.bloom=new zE({luminanceThreshold:.65,intensity:0,mipmapBlur:!0}),this.fxPass=new YE(this.camera,this.bloom),this.composer.addPass(this.fxPass),this.composer.setSize(this.heart.clientWidth||1600,this.heart.clientHeight||900),this.morphables=[this.dimPts,this.litPts,this.goalPts,a,o,this.planetPts,this.planetInnerPts,this.moonPts,l,this.guestPts,c,this.guestTails,u];for(const v of[this.goalPts,this.planetPts,this.planetInnerPts,this.moonPts,this.guestPts,this.guestTails])v.userData.orbitManaged=!0;this.goalPeriods=this.L.goals.map((v,S)=>60+S*15),this.planetPeriods=this.L.planets.map((v,S)=>40+S*5),this.guestPeriods=this.L.guests.map((v,S)=>8+S*2.3),this.goalPhase=this.L.goals.map(()=>0),this.planetPhase=this.L.planets.map(()=>0),this.guestPhase=this.L.guests.map(()=>0),this.guestDeepBase=this.L.guests.map(v=>v.deep.slice()),this.planetDeepBase=this.L.planets.map(v=>v.deep.slice()),this.goalDeepBase=this.L.goals.map(v=>v.deep.slice()),this.L.planets.forEach((v,S)=>{for(let b=0;b<Math.min(v.taskCount,5);b++)this.moonPlanet.push(S)}),this.moonDeepBase=[];for(let v=0;v<this.L.moons.deep.length;v+=3)this.moonDeepBase.push(this.L.moons.deep.slice(v,v+3));const p=this.guestTails;this.L.guests.forEach((v,S)=>{const b=[];for(let E=0;E<10;E++){const x=(S*10+E)*3;b.push([p.userData.deep[x]-v.deep[0],p.userData.deep[x+1]-v.deep[1],p.userData.deep[x+2]-v.deep[2]])}this.tailOffsets.push(b)});const _=(v,S)=>{const b=v.geometry.attributes.position.array;return[b[S*3],b[S*3+1],b[S*3+2]]};this.hoverables=[{title:"北极星",info:r.north_star.split(/[，。]/)[0],pos:()=>[0,0,0]},...this.L.goals.map((v,S)=>({title:v.title,info:"目标恒星",pos:()=>_(this.goalPts,S)})),...this.L.planets.map((v,S)=>({title:v.title,info:`${v.status==="active"?"行星 · 在轨":"行星 · 归档"} · 任务 ${v.taskCount}`+(v.progress!==null&&v.progress!==void 0?` · 进度 ${Math.round(v.progress*100)}%`:""),pos:()=>_(this.planetPts,S)})),...this.L.guests.map((v,S)=>({title:v.title,info:`客星 · ${v.date} · ${v.strength}${v.review==="needs_review"?" · 待评审":""}`,pos:()=>_(this.guestPts,S)}))],this.clickables=[{kind:"north",idx:-1,title:"北极星",pos:()=>[0,0,0]},...this.L.goals.map((v,S)=>({kind:"goal",idx:S,title:v.title,pos:()=>_(this.goalPts,S)})),...this.L.planets.map((v,S)=>({kind:"planet",idx:S,title:v.title,pos:()=>_(this.planetPts,S)})),...this.L.guests.map((v,S)=>({kind:"guest",idx:S,title:v.title,pos:()=>_(this.guestPts,S)})),...this.L.lit.skills.map((v,S)=>({kind:"skill",idx:S,title:v.label,pos:()=>_(this.litPts,S)}))],this.selRing=new Sd(new Dt().setFromPoints(this.circlePoints(3.2,48)),new hh({color:Ow,transparent:!0,opacity:.8,depthWrite:!1})),this.selRing.visible=!1,this.chart.add(this.selRing);const M=new ResizeObserver(()=>this.onResize());M.observe(this.heart),this.resizeObserver=M,window.addEventListener("pointermove",this.onPointerMoveWindow,{passive:!0}),window.addEventListener("pointermove",this.onPointerActive,{passive:!0}),window.addEventListener("click",this.onClickWindow),window.addEventListener("keydown",this.onKeydown),window.addEventListener("wheel",this.onWheel,{passive:!0}),this.canvas.addEventListener("pointerdown",v=>{this.coarsePointer||this.state.t>=.5||(this.dragging=!0,this.dragLastX=v.clientX,this.dragLastT=performance.now(),this.dragDist=0,this.spinVel=0,this.canvas.setPointerCapture(v.pointerId))}),this.canvas.addEventListener("pointermove",v=>{if(!this.dragging)return;const S=performance.now(),b=v.clientX-this.dragLastX,E=Math.max((S-this.dragLastT)/1e3,.008);this.dragLastX=v.clientX,this.dragLastT=S,this.dragDist+=Math.abs(b);const x=b*.004;this.chart.rotation.z+=x,this.spinVel=this.spinVel*.75+x/E*.25});const y=()=>{this.dragging=!1};this.canvas.addEventListener("pointerup",y),this.canvas.addEventListener("pointercancel",y),this.coarsePointer&&(this.controls=new ty(this.camera,this.canvas),this.controls.enableRotate=!1,this.controls.enableDamping=!0,this.controls.dampingFactor=.08,this.controls.enableZoom=!0,this.controls.zoomSpeed=.9,this.controls.enablePan=!0,this.controls.panSpeed=.8),this.guestBaseOpacity=new Float32Array(this.guestPts.geometry.attributes.aOpacity.array),this.onResize(),this.applyMorph(),i.initialState==="deepspace"&&this.goTo(1,!0),this.loop()}goTo(e,t=!1){if(this.tween&&this.tween.kill(),this.closeDetail(),t||this.reducedMotion){this.state.t=e,this.applyMorph();return}this.tween=ng.to(this.state,{t:e,duration:2.4,ease:"power2.inOut",onUpdate:()=>this.applyMorph()})}toggle(){this.goTo(this.state.t>.5?0:1)}deselect(){this.closeDetail()}dispose(){var e,t;this.disposed=!0,(e=this.resizeObserver)==null||e.disconnect(),cancelAnimationFrame(this.rafId),this.tween&&this.tween.kill(),window.removeEventListener("pointermove",this.onPointerMoveWindow),window.removeEventListener("pointermove",this.onPointerActive),window.removeEventListener("click",this.onClickWindow),window.removeEventListener("keydown",this.onKeydown),window.removeEventListener("wheel",this.onWheel),(t=this.controls)==null||t.dispose(),this.scene.traverse(r=>{const i=r;i.geometry&&i.geometry.dispose();const s=i.material;Array.isArray(s)?s.forEach(a=>a.dispose()):s==null||s.dispose()}),this.composer.dispose(),this.renderer.dispose();for(const r of[this.bgStone,this.bgDeep,this.bgDusk,this.vignette,this.tooltip])r.remove();this.canvas.remove()}fitPlanCamera(){const e=this.heart.clientWidth||1600,t=this.heart.clientHeight||900,r=Math.tan(this.camera.fov*Math.PI/360);this.camPlan.pos.z=(Ho+16)/(r*Math.min(1,e/t))}bakeBackgrounds(){const e=yf("rgb"),t=(a,o,l)=>{const c=e(Lw([a,o],"oklch")(l));return[Math.round(c.r*255),Math.round(c.g*255),Math.round(c.b*255)]},r=t("#1c2c4e","#10172c",.4),i=t("#182642","#0d1322",.4),s=a=>{const c=document.createElement("canvas");c.width=1024,c.height=640;const u=c.getContext("2d"),f=a==="stone",h=a==="dusk",d=f?[37,64,94]:h?r:[36,44,62],m=f?[29,52,80]:h?i:[26,31,46],g=u.createLinearGradient(0,0,0,640);g.addColorStop(0,`rgb(${d.join(",")})`),g.addColorStop(1,`rgb(${m.join(",")})`),u.fillStyle=g,u.fillRect(0,0,1024,640);const p=Mi(f?41:h?43:42);for(let v=0;v<9;v++){const S=p()*1024,b=p()*640,E=120+p()*260,x=p()>.5,w=(f?.05:h?.04:.035)*(.7+p()*.6),R=u.createRadialGradient(S,b,0,S,b,E);R.addColorStop(0,x?`rgba(70,98,132,${w})`:`rgba(10,20,36,${w})`),R.addColorStop(1,"rgba(0,0,0,0)"),u.fillStyle=R,u.fillRect(S-E,b-E,E*2,E*2)}if(h){const v=u.createRadialGradient(512,396.8,0,512,396.8,348.16);v.addColorStop(0,"rgba(196,138,64,0.13)"),v.addColorStop(.55,"rgba(150,100,52,0.05)"),v.addColorStop(1,"rgba(150,100,52,0)"),u.fillStyle=v,u.fillRect(0,0,1024,640)}const _=u.getImageData(0,0,1024,640),M=f?.028:h?.04:.05,y=f?.045:h?.032:.02;for(let v=0;v<640;v++){const S=v/640;for(let b=0;b<1024;b++){const E=b/1024,x=Math.exp(-Math.pow((E*.82+S*.57-.78)*5,2))*M,w=(p()-.5)*y,R=(v*1024+b)*4,L=(x+w)*255;_.data[R]=Math.max(0,Math.min(255,_.data[R]+L*.9)),_.data[R+1]=Math.max(0,Math.min(255,_.data[R+1]+L*.88)),_.data[R+2]=Math.max(0,Math.min(255,_.data[R+2]+L*.82))}}return u.putImageData(_,0,0),c};this.bgStone.style.backgroundImage=`url(${s("stone").toDataURL("image/png")})`,this.bgDusk.style.backgroundImage=`url(${s("dusk").toDataURL("image/png")})`,this.bgDusk.style.opacity="0",this.bgDeep.style.backgroundImage=`url(${s("deep").toDataURL("image/png")})`,this.bgDeep.style.opacity="0"}applyBackground(e,t){e<=t?(this.bgDusk.style.opacity=String(e/t),this.bgDeep.style.opacity="0"):(this.bgDusk.style.opacity="1",this.bgDeep.style.opacity=String((e-t)/(1-t)))}lineMat(e,t,r,i=1){const s=new hh({color:e,transparent:!0,opacity:t,depthWrite:!1});return this.fadeMats.push({mat:s,plan:t,deep:r,ch:i}),s}circlePoints(e,t=160){const r=[];for(let i=0;i<=t;i++){const s=i/t*Math.PI*2;r.push(new X(e*Math.cos(s),e*Math.sin(s),0))}return r}buildLinework(){const e=this.L,t=this.lineMat(En,.42,.2,2),r=this.lineMat(En,.55,0,1),i=this.lineMat(En,.18,0,1),s=this.lineMat(En,.08,0,1),a=this.lineMat(En,.5,0,2),o=this.lineMat(En,.52,.15,2),l=this.lineMat(En,.35,0,2),c=(d,m,g=!1)=>{const p=new Dt().setFromPoints(d),_=g?new Sd(p,m):new Jh(p,m);return this.chart.add(_),_},u=Mi(53),f=(d,m,g,p)=>{const _=[];for(let M=0;M<=4;M++){const y=d+(m-d)*M/4,S=(g+(M>0&&M<4?(u()-.5)*1.4:0))*Math.PI/180;_.push(new X(y*Math.cos(S),y*Math.sin(S),0))}c(_,p)};for(const[d,m]of[[Na,t],[Iw,t],[At,r],[vu,a],[Ho,a]])c(this.circlePoints(d),m,!0);{const d=[];for(let m=18;m<=342;m+=2){const g=m*Math.PI/180;d.push(new X(Ca*Math.cos(g),Ca*Math.sin(g),0))}c(d,t)}{const d=[];for(let g=0;g<360;g+=6){const p=g*Math.PI/180,_=At+(g%30===0?3.25:1.5);d.push(new X(At*Math.cos(p),At*Math.sin(p),0)),d.push(new X(_*Math.cos(p),_*Math.sin(p),0))}const m=new Dt().setFromPoints(d);this.chart.add(new Pr(m,r))}const h=d=>(d=d%360,d>180&&(d-=360),d<-180&&(d+=360),d);for(const d of e.sectors){Math.abs(h(d.start))>=12&&f(Ca,At,d.start,i);const m=Math.max(1,Math.round(d.count/6)),g=[];for(let _=1;_<m;_++)g.push(_/m+(u()-.5)*.5/m);g.sort();for(const _ of g){const M=d.start+d.width*_;Math.abs(h(M))>=12&&f(Ca,At,M,s)}const p=d.start*Math.PI/180;c([new X(vu*Math.cos(p),vu*Math.sin(p),0),new X(Ho*Math.cos(p),Ho*Math.sin(p),0)],a)}{const d=[],m=e.lit.plan;for(let p=0;p<e.lit.links.length;p+=2){const _=e.lit.links[p]*3,M=e.lit.links[p+1]*3;d.push(new X(m[_],m[_+1],0)),d.push(new X(m[M],m[M+1],0))}const g=new Dt().setFromPoints(d);this.chart.add(new Pr(g,o))}{const d=[],m=e.court.plan;for(const[p,_]of e.court.links)d.push(new X(m[p*3],m[p*3+1],0)),d.push(new X(m[_*3],m[_*3+1],0));const g=new Dt().setFromPoints(d);this.chart.add(new Pr(g,l))}c(this.circlePoints(4.2,64),this.lineMat(En,.55,0,2),!0)}makePoints(e){const{plan:t,deep:r,size:i,opacity:s,core:a,ring:o,color:l}=e,c=new Dt;c.setAttribute("position",new kt(new Float32Array(t),3)),c.setAttribute("aSize",new kt(new Float32Array(i),1)),c.setAttribute("aOpacity",new kt(new Float32Array(s),1)),c.setAttribute("aCore",new kt(new Float32Array(a),1)),c.setAttribute("aRing",new kt(new Float32Array(o),1)),c.setAttribute("aColor",new kt(new Float32Array(l),3));const u=new an({transparent:!0,depthWrite:!1,blending:zr,uniforms:{uScale:{value:1},uGlobal:{value:1}},vertexShader:`
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
      `}),f=new $_(c,u);return f.userData.plan=new Float32Array(t),f.userData.deep=new Float32Array(r),this.chart.add(f),f}makeGlowTexture(){const e=document.createElement("canvas");e.width=e.height=128;const t=e.getContext("2d"),r=t.createRadialGradient(64,64,0,64,64,64);return r.addColorStop(0,"rgba(255,255,255,1)"),r.addColorStop(.25,"rgba(255,255,255,0.35)"),r.addColorStop(1,"rgba(255,255,255,0)"),t.fillStyle=r,t.fillRect(0,0,128,128),new J_(e)}addLabel(e,t={}){const{size:r=3.4,color:i=En,font:s=Hw,pos:a=[0,0,0],deepPos:o=null,rotZ:l=0,anchorX:c="center",fade:u="band"}=t,f=new xh;return f.text=e,f.font=s,f.fontSize=r,f.color=i,f.anchorX=c,f.anchorY="middle",f.position.set(a[0],a[1],a[2]??0),f.rotation.z=l,f.material.transparent=!0,f.outlineWidth="5%",f.outlineColor=726566,f.outlineOpacity=.85,this.chart.add(f),this.labelObjs.push({t:f,fade:u,planPos:a.slice(),deepPos:o?o.slice():null}),f}addSegmentedLabel(e,t){const{size:r=3.6,color:i=15652502,pos:s,align:a="left",fade:o="goal",goalIdx:l=-1}=t,c=e.split(/([A-Za-z0-9.]+)/).filter(Boolean),u={goalIdx:l,segs:[],base:[],anchor:s.slice()},f=c.map(d=>{const m=/^[A-Za-z0-9.]+$/.test(d),g=new xh;return g.text=d,g.font=m?Vw:lm,g.fontSize=r,g.color=i,g.anchorX="left",g.anchorY="middle",g.material.transparent=!0,g.outlineWidth="5%",g.outlineColor=726566,g.outlineOpacity=.85,this.chart.add(g),this.labelObjs.push({t:g,fade:o,planPos:s.slice(),deepPos:null}),u.segs.push(g),g});l>=0&&this.goalLabelGroups.push(u),this.segPending+=f.length;let h=f.length;f.forEach(d=>d.sync(()=>{if(this.segPending-=1,h-=1,h===0){const m=f.map(_=>{const M=_.textRenderInfo&&_.textRenderInfo.blockBounds;return M?Math.max(.1,M[2]-M[0]):_.text.length*r*.6}),g=m.reduce((_,M)=>_+M,0)+.4*(f.length-1);let p=s[0]-(a==="right"?g:a==="center"?g/2:0);f.forEach((_,M)=>{_.position.set(p,s[1],0),p+=m[M]+.4}),u.base=f.map(_=>[_.position.x,_.position.y])}}))}buildLabels(){const e=this.L;for(const s of e.sectors){const a=s.start+s.width/2,o=Array.from(s.name),l=3.4*1.25/xu*(180/Math.PI),c=a-l*(o.length-1)/2;o.forEach((u,f)=>{const d=(c+f*l)*Math.PI/180;this.addLabel(u,{size:3.2,color:En,font:lm,fade:"band",pos:[xu*Math.cos(d),xu*Math.sin(d),0],rotZ:d+Math.PI/2})})}e.goals.forEach((s,a)=>{const o=Math.cos(s.angle*Math.PI/180),l=o>.35?"left":o<-.35?"right":"center",c=Na+8,u=s.angle*Math.PI/180;this.addSegmentedLabel(s.title,{size:3.6,color:15652502,align:l,goalIdx:a,pos:[c*Math.cos(u)+(l==="left"?1:l==="right"?-1:0),c*Math.sin(u),0]})});const t=this.snapshot.north_star.split(/[，。]/)[0],r=t.indexOf("成为"),i=r>0?[t.slice(0,r+2),t.slice(r+2)]:[t,""];this.addLabel(i[0],{size:3.8,color:En,font:cm,anchorX:"left",pos:[6.5,3.4,0],deepPos:[10.5,-8.5,0],fade:"north"}),this.addLabel(i[1],{size:3.8,color:15652502,font:cm,anchorX:"left",pos:[6.5,-2.6,0],deepPos:[10.5,-13.6,0],fade:"north"}),this.labelsPending=this.labelObjs.length;for(const{t:s}of this.labelObjs)s.sync(()=>{this.labelsPending-=1})}applyMorph(){var M,y;const e=this.state.t,t=Mu(e,this.state.w1),r=Mu(e,this.state.w2),i=Mu(e,this.state.w3);this.state.ch1=t,this.state.ch2=r,this.state.ch3=i;for(const v of this.morphables){if(v.userData.orbitManaged)continue;const S=v.geometry.attributes.position,b=v.userData.plan,E=v.userData.deep,x=S.array;for(let w=0;w<x.length;w++)x[w]=b[w]+(E[w]-b[w])*r;S.needsUpdate=!0}this.chart.rotation.x=-1.05*r,this.camera.position.lerpVectors(this.camPlan.pos,this.camDeep.pos,r),this.camera.lookAt(new X().lerpVectors(this.camPlan.look,this.camDeep.look,r));for(const{mat:v,plan:S,deep:b,ch:E}of this.fadeMats){const x=E===1?t:E===3?i:r;v.opacity=S+(b-S)*x}for(const{t:v,fade:S,planPos:b,deepPos:E}of this.labelObjs)S==="band"?(v.material.opacity=1-r,v.visible=r<.98):S==="north"&&E&&(v.material.opacity=1-.25*r,v.position.set(b[0]+(E[0]-b[0])*r,b[1]+(E[1]-b[1])*r,0));for(const v of this.glows){v.mat.opacity=v.maxOpacity*i,v.spr.visible=v.mat.opacity>.004;const S=v.getPos();v.spr.position.set(S[0],S[1],S[2])}for(const v of this.nebulae)v.mat.opacity=v.op*i,v.spr.visible=v.mat.opacity>.004;const s=Math.exp(-Math.pow((r-this.state.duskPos)/.13,2))*this.state.duskAmt,a=this.glows[0];if(s>.01){a.mat.opacity=Math.min(1,Math.max(a.mat.opacity,a.maxOpacity*s*.6)),a.spr.visible=!0;const v=20*(1+.55*s);a.spr.scale.set(v,v,1)}else a.spr.scale.set(20,20,1);const o=this.dimPts.geometry.attributes.aOpacity,l=this.dimPts.geometry.attributes.aSize,c=this.dimPts.geometry.attributes.aRing,u=this.dimPts.userData.baseOpacity,f=this.dimPts.userData.baseSize,h=this.dimPts.userData.baseRing,d=this.dimPts.userData.deepOpScale,m=this.dimPts.userData.deepSizeScale,g=this.dimPts.userData.filler;for(let v=0;v<o.array.length;v++){const S=g[v]?this.state.density:1;o.array[v]=u[v]*S*(1+(d[v]-1)*i),l.array[v]=f[v]*(1+(m[v]-1)*i),c.array[v]=h[v]*(1-.55*i)}o.needsUpdate=!0,l.needsUpdate=!0,c.needsUpdate=!0,this.applyBackground(r,this.state.duskPos),this.fxPass.enabled=!this.softGL&&i>.02,this.bloom.intensity=.7*i*this.state.bloom,this.vignette.style.opacity=String(.55+.45*r);const p=String(1-r),_=this.opts.domRefs;_!=null&&_.cartouche&&(_.cartouche.style.opacity=p),_!=null&&_.briefing&&(_.briefing.style.opacity=p),_!=null&&_.toggle&&(_.toggle.textContent=e>.5?"→ 图态":"→ 境态"),(y=(M=this.opts).onMorph)==null||y.call(M,e)}screenOf(e){const t=new X(e[0],e[1],e[2]??0);this.chart.localToWorld(t),t.project(this.camera);const r=this.heart.getBoundingClientRect();return[r.left+(t.x*.5+.5)*r.width,r.top+(-t.y*.5+.5)*r.height]}onPointerMove(e){this.hoverIdx=-1;let t=26;this.hoverables.forEach((r,i)=>{const[s,a]=this.screenOf(r.pos()),o=Math.hypot(s-e.clientX,a-e.clientY);o<t&&(t=o,this.hoverIdx=i)})}updateTooltip(){const e=this.tooltip;if(this.hoverIdx<0||!this.hoverables[this.hoverIdx]){e.style.display="none";return}const t=this.hoverables[this.hoverIdx],[r,i]=this.screenOf(t.pos());e.innerHTML='<div class="tt-title"></div><div class="tt-info"></div>',e.querySelector(".tt-title").textContent=t.title,e.querySelector(".tt-info").textContent=t.info,e.style.display="block";const s=e.offsetWidth;e.style.left=Math.min(window.innerWidth-s-12,r+16)+"px",e.style.top=Math.max(10,i-44)+"px"}detailRows(e){const t=this.snapshot;if(e.kind==="north")return[["类型","北极星"],["铭文",t.north_star]];if(e.kind==="goal"){const i=t.goals[e.idx];return[["状态",i.status],["起始",i.start||"—"],["目标",i.target||"—"],["铭文",i.summary||"—"]]}if(e.kind==="planet"){const i=t.projects[e.idx],s=this.L.planets[e.idx].goalIndex;return[["状态",i.status==="active"?"在轨":"归档"],["所属目标",s>=0?t.goals[s].title:"（自由轨道）"],["任务",`${i.task_count} 项`],["进度",i.progress===null||i.progress===void 0?"—":`${Math.round(i.progress*100)}%`],["时间范围",i.time_range||"—"]]}if(e.kind==="guest"){const i=t.evidence.find(s=>s.id===this.L.guests[e.idx].id)??this.L.guests[e.idx];return[["类型","type"in i?i.type:"—"],["强度",i.strength||"—"],["日期",i.date||"—"],["评审","review_status"in i&&i.review_status==="needs_review"?"待评审":"已入座"],["摘要","summary"in i&&i.summary?i.summary:"—"]]}const r=this.L.lit.skills[e.idx];return[["类别",r.category],["状态",r.status],["关联证据",`${r.evidenceCount} 条`]]}openDetail(e){var r,i;this.selectedIdx=e;const t=this.clickables[e];(i=(r=this.opts).onSelect)==null||i.call(r,{kind:t.kind,title:t.title,rows:this.detailRows(t)})}closeDetail(){var e,t;this.selectedIdx<0||(this.selectedIdx=-1,this.selRing.visible=!1,(t=(e=this.opts).onSelect)==null||t.call(e,null))}onClick(e){if(this.dragDist>6){this.dragDist=0;return}if(e.target.closest("[data-starmap-ui]"))return;let r=-1,i=26;this.clickables.forEach((s,a)=>{const[o,l]=this.screenOf(s.pos()),c=Math.hypot(o-e.clientX,l-e.clientY);c<i&&(i=c,r=a)}),r>=0?this.openDetail(r):this.closeDetail()}updatePointScale(){const t=this.renderer.domElement.height/(2*Math.tan(this.camera.fov*Math.PI/360));for(const r of this.morphables){const i=r;i.isPoints&&(i.material.uniforms.uScale.value=t)}}onResize(){const e=this.heart.clientWidth||1,t=this.heart.clientHeight||1;this.renderer.setSize(e,t),this.composer.setSize(e,t),this.camera.aspect=e/t,this.camera.updateProjectionMatrix(),this.fitPlanCamera(),this.controls&&(this.controls.minDistance=this.camPlan.pos.z*.65,this.controls.maxDistance=this.camPlan.pos.z*1.6),this.updatePointScale(),this.applyMorph()}loop(){if(this.disposed)return;this.rafId=requestAnimationFrame(()=>this.loop());const e=Math.min(this.clock.getDelta(),.1),t=this.clock.elapsedTime,{ch2:r,ch3:i}=this.state,s=this.L,a=performance.now(),l=this.dragging||this.hoverIdx>=0||this.selectedIdx>=0||a-this.lastPointerActive<3e3||this.reducedMotion?0:1;this.spinFactor+=(l-this.spinFactor)*Math.min(1,e/.8);const c=Math.PI*2/3600;this.chart.rotation.z+=e*c*this.spinFactor*(1+2.5*Math.sin(r*Math.PI)),!this.dragging&&Math.abs(this.spinVel)>1e-4&&(this.chart.rotation.z+=this.spinVel*e,this.spinVel*=Math.exp(-e/1.2));const u=(h,d,m)=>[h*Math.cos(m)-d*Math.sin(m),h*Math.sin(m)+d*Math.cos(m)];{const h=this.goalPts.geometry.attributes.position,d=s.goals.map((v,S)=>{const b=this.goalDeepBase[S];this.goalPhase[S]+=e*(2*Math.PI/this.goalPeriods[S])*i;const[E,x]=u(b[0],b[1],this.goalPhase[S]);return[v.plan[0]+(b[0]-v.plan[0])*r+(E-b[0]),v.plan[1]+(b[1]-v.plan[1])*r+(x-b[1]),v.plan[2]+(b[2]-v.plan[2])*r]});d.forEach((v,S)=>h.setXYZ(S,v[0],v[1],v[2])),h.needsUpdate=!0;for(const v of this.goalLabelGroups){if(!v.base.length)continue;const S=d[v.goalIdx],b=s.goals[v.goalIdx].plan,E=this.goalDeepBase[v.goalIdx],x=b[0]+(E[0]-b[0])*r,w=b[1]+(E[1]-b[1])*r,R=S[0]-x,L=S[1]-w;v.segs.forEach((A,U)=>A.position.set(v.base[U][0]+R,v.base[U][1]+L,0))}const m=this.planetPts.geometry.attributes.position,g=this.planetInnerPts.geometry.attributes.position,p=this.moonPts.geometry.attributes.position,_=s.planets.map((v,S)=>{const b=this.planetDeepBase[S];this.planetPhase[S]+=e*(2*Math.PI/this.planetPeriods[S])*i;const E=v.goalIndex,x=E>=0?this.goalDeepBase[E]:[0,0,0],w=E>=0?d[E]:[0,0,0],[R,L]=u(b[0]-x[0],b[1]-x[1],this.planetPhase[S]),A=v.plan[0]+(b[0]-v.plan[0])*r,U=v.plan[1]+(b[1]-v.plan[1])*r;return[A+(w[0]-x[0])+(R-(b[0]-x[0])),U+(w[1]-x[1])+(L-(b[1]-x[1])),v.plan[2]+(b[2]-v.plan[2])*r]});_.forEach((v,S)=>{m.setXYZ(S,v[0],v[1],v[2]),g.setXYZ(S,v[0],v[1],v[2])}),m.needsUpdate=!0,g.needsUpdate=!0,this.moonDeepBase.forEach((v,S)=>{const b=this.moonPlanet[S];b!==void 0&&p.setXYZ(S,v[0]+(_[b][0]-this.planetDeepBase[b][0]),v[1]+(_[b][1]-this.planetDeepBase[b][1]),v[2])}),p.needsUpdate=!0;const M=this.guestPts.geometry.attributes.position,y=this.guestTails.geometry.attributes.position;s.guests.forEach((v,S)=>{const b=this.guestDeepBase[S];this.guestPhase[S]+=e*(2*Math.PI/this.guestPeriods[S])*i;const E=7*i,x=v.plan[0]+(b[0]-v.plan[0])*r+E*Math.cos(this.guestPhase[S]+S*1.3),w=v.plan[1]+(b[1]-v.plan[1])*r+E*Math.sin(this.guestPhase[S]+S*1.3),R=v.plan[2]+(b[2]-v.plan[2])*r;M.setXYZ(S,x,w,R),this.guestGlows[S].spr.position.set(x,w,R),this.tailOffsets[S].forEach((A,U)=>y.setXYZ(S*10+U,x+A[0]*r,w+A[1]*r,R+A[2]*r))}),M.needsUpdate=!0,y.needsUpdate=!0}const f=h=>h<.25?.5-.5*Math.cos(h/.25*Math.PI):h<.45?1:.5+.5*Math.cos((h-.45)/.55*Math.PI);if(this.reducedMotion)for(const h of this.guestGlows)h.mat.opacity=(.34+.3*i)*.925,h.spr.visible=h.mat.opacity>.004;else for(const h of this.guestGlows){const d=.34+.3*i,m=h.breathe?f((t/11+h.idx*.31)%1):.4;h.mat.opacity=d*(.85+.15*m),h.spr.visible=h.mat.opacity>.004;const g=5.5*(1+.4*i);h.spr.scale.set(g,g,1)}{const h=this.guestPts.geometry.attributes.aOpacity;let d=!1;for(let m=0;m<h.array.length;m++)h.array[m]!==this.guestBaseOpacity[m]&&(h.array[m]=this.guestBaseOpacity[m],d=!0);d&&(h.needsUpdate=!0)}if(this.updateTooltip(),this.selectedIdx>=0){const h=this.clickables[this.selectedIdx].pos();this.selRing.visible=!0,this.selRing.position.set(h[0],h[1],h[2]??0);const d=this.reducedMotion?1:1+.04*Math.sin(t*3);this.selRing.scale.set(d,d,1)}if(this.controls){this.controls.enabled=this.state.t<.5,this.controls.update();const h=this.controls.target,d=Math.max(-70,Math.min(70,h.x)),m=Math.max(-70,Math.min(70,h.y));(d!==h.x||m!==h.y)&&(this.camera.position.x+=d-h.x,this.camera.position.y+=m-h.y,h.x=d,h.y=m,h.z=0)}this.fxPass.enabled?this.composer.render():this.renderer.render(this.scene,this.camera)}}const Xw="/assets/title-v2-b-ibfvihIe.svg",Yw={north:{path:"goals",label:"前往目标 →"},goal:{path:"goals",label:"前往目标 →"},planet:{path:"projects",label:"前往项目 →"},guest:{path:"evidence-review",label:"前往评审 →"},skill:{path:"skill-tree",label:"前往技能树 →"}};function Kw({snapshot:n}){const{name:e=""}=zg(),t=gi.useRef(null),r=gi.useRef(null),i=gi.useRef(null),s=gi.useRef(null),a=gi.useRef(null),o=gi.useRef(null),[l,c]=gi.useState(null),[u,f]=gi.useState(!1);gi.useEffect(()=>{const m=t.current,g=r.current;if(!m||!g)return;let p=null;try{p=new Ww(m,g,n,{onSelect:c,domRefs:{cartouche:i.current,briefing:s.current,toggle:a.current}})}catch{f(!0);return}return o.current=p,()=>{p==null||p.dispose(),o.current=null}},[n]);const h=gi.useMemo(()=>`「${n.counts.evidence_needs_review} 条客星待评审，${n.counts.projects_active} 颗行星在轨。」`,[n]),d=l?Yw[l.kind]:null;return Bt.jsxs("div",{className:"starmap-root",ref:t,"data-testid":"starmap-root",children:[Bt.jsxs("div",{className:"starmap-layout",children:[Bt.jsx("div",{className:"starmap-mount-top",children:Bt.jsx("img",{className:"starmap-cartouche",ref:i,src:Xw,alt:"成长星图"})}),Bt.jsx("div",{className:"starmap-heart",ref:r,"data-testid":"starmap-heart"}),Bt.jsx("div",{className:"starmap-mount-bottom",children:Bt.jsx("div",{className:"starmap-briefing",ref:s,"data-testid":"starmap-briefing",children:h})})]}),!u&&Bt.jsx("button",{type:"button",className:"starmap-toggle",ref:a,"data-starmap-ui":!0,"data-testid":"starmap-toggle",onClick:()=>{var m;return(m=o.current)==null?void 0:m.toggle()},children:"→ 境态"}),Bt.jsx("div",{className:`starmap-detail${l?" open":""}`,"data-starmap-ui":!0,"data-testid":"starmap-detail",children:l&&Bt.jsxs(Bt.Fragment,{children:[Bt.jsx("h3",{children:l.title}),Bt.jsx("dl",{children:l.rows.map(([m,g])=>Bt.jsxs("div",{children:[Bt.jsx("dt",{children:m}),Bt.jsx("dd",{children:g})]},m))}),d&&Bt.jsx(Gg,{className:"starmap-detail-link",to:`/p/${encodeURIComponent(e)}/${d.path}`,children:d.label})]})}),u&&Bt.jsxs("div",{className:"starmap-fallback","data-testid":"starmap-fallback",children:[Bt.jsx("div",{className:"fb-title",children:"成长星图"}),Bt.jsx("div",{className:"fb-line",children:n.north_star||"尚未设置北极星。"}),Bt.jsx("div",{className:"fb-line",children:h}),Bt.jsx("div",{className:"fb-line",children:"此浏览器不支持 WebGL，以上为静态简报。"})]})]})}export{Kw as StarmapView};
