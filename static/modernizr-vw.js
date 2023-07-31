/*! modernizr 3.5.0 (Custom Build) | MIT *
 * https://modernizr.com/download/?-cssvwunit-setclasses !*/
!function(e,n,t){function s(e,n){return typeof e===n}function o(){var e,n,t,o,a,r,i;for(var l in c)if(c.hasOwnProperty(l)){if(e=[],n=c[l],n.name&&(e.push(n.name.toLowerCase()),n.options&&n.options.aliases&&n.options.aliases.length))for(t=0;t<n.options.aliases.length;t++)e.push(n.options.aliases[t].toLowerCase());for(o=s(n.fn,"function")?n.fn():n.fn,a=0;a<e.length;a++)r=e[a],i=r.split("."),1===i.length?Modernizr[i[0]]=o:(!Modernizr[i[0]]||Modernizr[i[0]]instanceof Boolean||(Modernizr[i[0]]=new Boolean(Modernizr[i[0]])),Modernizr[i[0]][i[1]]=o),f.push((o?"":"no-")+i.join("-"))}}function a(e){var n=p.className,t=Modernizr._config.classPrefix||"";if(h&&(n=n.baseVal),Modernizr._config.enableJSClass){var s=new RegExp("(^|\\s)"+t+"no-js(\\s|$)");n=n.replace(s,"$1"+t+"js$2")}Modernizr._config.enableClasses&&(n+=" "+t+e.join(" "+t),h?p.className.baseVal=n:p.className=n)}function r(n,t,s){var o;if("getComputedStyle"in e){o=getComputedStyle.call(e,n,t);var a=e.console;if(null!==o)s&&(o=o.getPropertyValue(s));else if(a){var r=a.error?"error":"log";a[r].call(a,"getComputedStyle returning null, its possible modernizr test results are inaccurate")}}else o=!t&&n.currentStyle&&n.currentStyle[s];return o}function i(){return"function"!=typeof n.createElement?n.createElement(arguments[0]):h?n.createElementNS.call(n,"http://www.w3.org/2000/svg",arguments[0]):n.createElement.apply(n,arguments)}function l(){var e=n.body;return e||(e=i(h?"svg":"body"),e.fake=!0),e}function d(e,t,s,o){var a,r,d,f,c="modernizr",u=i("div"),h=l();if(parseInt(s,10))for(;s--;)d=i("div"),d.id=o?o[s]:c+(s+1),u.appendChild(d);return a=i("style"),a.type="text/css",a.id="s"+c,(h.fake?h:u).appendChild(a),h.appendChild(u),a.styleSheet?a.styleSheet.cssText=e:a.appendChild(n.createTextNode(e)),u.id=c,h.fake&&(h.style.background="",h.style.overflow="hidden",f=p.style.overflow,p.style.overflow="hidden",p.appendChild(h)),r=t(u,e),h.fake?(h.parentNode.removeChild(h),p.style.overflow=f,p.offsetHeight):u.parentNode.removeChild(u),!!r}var f=[],c=[],u={_version:"3.5.0",_config:{classPrefix:"",enableClasses:!0,enableJSClass:!0,usePrefixes:!0},_q:[],on:function(e,n){var t=this;setTimeout(function(){n(t[e])},0)},addTest:function(e,n,t){c.push({name:e,fn:n,options:t})},addAsyncTest:function(e){c.push({name:null,fn:e})}},Modernizr=function(){};Modernizr.prototype=u,Modernizr=new Modernizr;var p=n.documentElement,h="svg"===p.nodeName.toLowerCase(),m=u.testStyles=d;m("#modernizr { width: 50vw; }",function(n){var t=parseInt(e.innerWidth/2,10),s=parseInt(r(n,null,"width"),10);Modernizr.addTest("cssvwunit",s==t)}),o(),a(f),delete u.addTest,delete u.addAsyncTest;for(var v=0;v<Modernizr._q.length;v++)Modernizr._q[v]();e.Modernizr=Modernizr}(window,document);