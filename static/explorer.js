'use strict';
const $ = id => document.getElementById(id);
const state = {tab:'overview', tokens:{}, frames:[], frame:0, timer:null, events:[], map:null, markers:null, tiles:null, media:{collection:'webb',group:'space',page:1,payload:null,catalog:null}};
const dateString = d => d.toLocaleDateString('en-CA');
const yesterday = new Date(Date.now()-86400000).toISOString().slice(0,10);
$('today').textContent = new Date().toLocaleDateString('ru-RU',{day:'numeric',month:'long',year:'numeric'});
$('epic-date').max = $('map-date').max = new Date().toISOString().slice(0,10);
$('map-date').value = yesterday;
function node(tag, text, className) { const e=document.createElement(tag); if(text!==undefined)e.textContent=text;if(className)e.className=className;return e; }
function url(value) { try { const u=new URL(value);return u.protocol==='https:'?u.href:''; }catch{return '';} }
function external(label, href) {const a=node('a',label); a.href=url(href);a.target='_blank';a.rel='noopener';if(!a.href)a.hidden=true;return a;}
function stamp(value) {if(!value)return '';const d=new Date(value);return isNaN(d)?value:d.toLocaleString('ru-RU',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'});}
function sourceStatus(id, result) {
 const e=$(id);const labels={ready:'Данные получены',stale:'Сохранённые данные',loading:'Загружаем данные…',error:'Данные недоступны'};
 e.textContent=`${result.source} · ${labels[result.status] || result.status}${result.updated_at?' · Обновлено '+stamp(result.updated_at):''}${result.error?' · '+result.error:''}`;
 e.classList.toggle('warn',['error','stale'].includes(result.status));
}
async function load(source, params, render, attempt=0, token=null) {
 const key=source;
 if(token===null)token=state.tokens[key]=(state.tokens[key]||0)+1;
 try {
  const response=await fetch('/api/explore/'+source+'?'+new URLSearchParams(params),{signal:AbortSignal.timeout(10000)});
  const data=await response.json();
  if(token!==state.tokens[key])return;
  if(!response.ok)throw new Error(data.error||'Не удалось загрузить данные');
  sourceStatus(source+'-status',data);
  if(data.data!==null)render(data.data);
  else if(data.status==='error')emptyFor(source,'Источник временно недоступен. Попробуйте открыть раздел позднее.');
  if(data.refreshing && attempt<20)setTimeout(()=>load(source,params,render,attempt+1,token),1500);
 }catch(error) {
  if(token!==state.tokens[key])return;
  $(source+'-status').textContent=error.message || 'Нет соединения с сервером';
  $(source+'-status').classList.add('warn');
 }
}
function emptyFor(source,text) {const ids={rover:'rover-grid',media:'media-grid',weather:'weather-list',events:'events-list'};if(ids[source])$(ids[source]).replaceChildren(node('div',text,'empty'));if(source==='epic'){$('earth-empty').hidden=false;$('earth-empty').textContent=text;}}
function showPhoto(p) {
 $('dialog-image').src=url(p.image_url);$('dialog-image').alt=p.title||'Снимок NASA';
 $('dialog-title').textContent=p.title||'';$('dialog-description').textContent=p.description||p.date||'';
 $('dialog-credit').textContent=[p.credit?'Автор / источник: '+p.credit:'',p.date?'Дата в каталоге: '+p.date.slice(0,10):'',p.kind&&p.kind!=='image'?'Тип: '+kindLabel(p.kind):''].filter(Boolean).join(' · ');
 $('dialog-link').href=url(p.url||p.image_url);$('dialog-original').hidden=true;$('asset-status').textContent='';
 state.tokens.asset=(state.tokens.asset||0)+1;
 if(p.credit!==undefined&&p.id){load('asset',{id:p.id},data=>{if(url(data.original_url)){$('dialog-original').href=data.original_url;$('dialog-original').hidden=false;}});}
 $('photo-dialog').showModal();
}
function kindLabel(kind){return ({illustration:'Иллюстрация',diagram:'Схема / данные',hardware:'Аппарат / оборудование'})[kind]||'Снимок / наблюдение';}
$('close-dialog').onclick=()=>$('photo-dialog').close();
$('photo-dialog').addEventListener('click',e=>{if(e.target===$('photo-dialog')){const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)e.target.close();}});
function cards(target,items) {
 const fragment=document.createDocumentFragment();
 for(const p of items){const card=node('button',undefined,'photo-card');const img=node('img');img.src=url(p.image_url);img.alt=p.title||'Снимок NASA';img.loading='lazy';img.onerror=()=>{img.replaceWith(node('div','Изображение временно недоступно','placeholder'));};const caption=node('div',undefined,'caption');caption.append(node('h3',p.title),node('small',[p.date?.slice(0,10),p.sol!==undefined?'Sol '+p.sol:null,p.camera].filter(Boolean).join(' · ')));if(p.kind&&p.kind!=='image')caption.append(node('span',kindLabel(p.kind),'media-badge'));if(p.credit)caption.append(node('small',p.credit));card.append(img,caption);card.onclick=()=>showPhoto(p);fragment.append(card);}
 $(target).replaceChildren(items.length?fragment:node('div','Для этого запроса снимки не найдены.','empty'));
}
function loadAPOD() {load('apod',{},p=>{$('apod-title').textContent=p.title;$('apod-description').textContent=p.explanation;$('apod-link').href=url(p.url);$('apod-link').hidden=!url(p.url);if(p.media_type==='image'&&url(p.image_url)){const img=node('img');img.src=p.image_url;img.alt=p.title;img.onerror=()=>$('apod-image').replaceChildren(node('div','Снимок недоступен — публикацию можно открыть у NASA.','placeholder'));$('apod-image').replaceChildren(img);}else $('apod-image').replaceChildren(node('div','Сегодня NASA опубликовала видео. Откройте публикацию по ссылке.','placeholder'));$('apod-observed').textContent='Публикация: '+p.date+(p.copyright?' · '+p.copyright:'');});}
function loadRover(){load('rover',{rover:$('rover-select').value},p=>cards('rover-grid',p.items));}
async function initCollections(){
 if(state.media.catalog)return;
 try{
  const response=await fetch('/api/media/collections');if(!response.ok)throw new Error();
  state.media.catalog=await response.json();renderCollections();
 }catch{$('collection-description').textContent='Не удалось загрузить подборки. Доступен поиск ниже.';}
}
function renderCollections(){
 const catalog=state.media.catalog;if(!catalog)return;
 $('collection-groups').replaceChildren();
 for(const group of catalog.groups){const b=node('button',group.title);b.classList.toggle('selected',group.id===state.media.group);b.setAttribute('aria-pressed',String(group.id===state.media.group));b.onclick=()=>{state.media.group=group.id;const first=catalog.collections.find(c=>c.group===group.id);state.media.collection=first.id;state.media.page=1;renderCollections();loadMedia();};$('collection-groups').append(b);}
 $('collection-description').textContent=catalog.groups.find(g=>g.id===state.media.group)?.description||'';
 $('collection-topics').replaceChildren();
 for(const topic of catalog.collections.filter(c=>c.group===state.media.group)){const b=node('button',topic.title);b.classList.toggle('selected',topic.id===state.media.collection);b.setAttribute('aria-pressed',String(topic.id===state.media.collection));b.onclick=()=>{state.media.collection=topic.id;state.media.page=1;$('search-query').value='';renderCollections();loadMedia();};$('collection-topics').append(b);}
}
function renderMedia(payload){
 state.media.payload=payload;
 const filtered=$('media-observations').checked?payload.items.filter(p=>p.kind==='image'):payload.items;
 cards('media-grid',filtered);
 if(!filtered.length&&payload.items.length)$('media-grid').replaceChildren(node('div','На этой странице остались только иллюстрации, схемы или аппараты. Отключите фильтр или откройте следующую страницу.','empty'));
 $('media-title').textContent=payload.title;$('media-note').textContent=payload.note;
 $('media-page').textContent=`Страница ${payload.page} из ${Math.min(payload.pages,100)} · показано ${filtered.length} из ${payload.items.length} на странице`;
 $('media-prev').disabled=payload.page<=1;$('media-next').disabled=payload.page>=Math.min(payload.pages,100);
}
function loadMedia(){
 initCollections();state.media.payload=null;
 $('media-prev').disabled=$('media-next').disabled=true;
 $('media-grid').replaceChildren(node('div','Загружаем снимки…','empty'));
 const topic=state.media.catalog?.collections.find(c=>c.id===state.media.collection);
 $('media-title').textContent=topic?.title||$('search-query').value.trim()||'Космические снимки';
 $('media-note').textContent=topic?.note||'';
 const params={page:state.media.page};
 if(state.media.collection)params.collection=state.media.collection;else params.q=$('search-query').value.trim();
 load('media',params,p=>{renderMedia(p);$('media-status').textContent+=` · В каталоге: ${p.total}`;});
}
$('media-observations').onchange=()=>{if(state.media.payload)renderMedia(state.media.payload);};
$('media-prev').onclick=()=>{state.media.page--;loadMedia();};
$('media-next').onclick=()=>{state.media.page++;loadMedia();};
function loadAsteroids(){load('asteroids',{},p=>{const body=$('asteroids-body');body.replaceChildren();for(const x of p.items){const row=node('tr');const distance=node('td',x.distance_ld+' до Луны');distance.append(node('small',x.distance_km.toLocaleString('ru-RU')+' км'));row.append(node('td',x.name),node('td',x.date),distance,node('td',x.speed_kms+' км/с'),node('td',x.time_uncertainty||'—'));body.append(row);}if(!p.items.length){const cell=node('td','В заданном диапазоне сближений нет.');cell.colSpan=5;const row=node('tr');row.append(cell);body.append(row);}$('asteroid-summary').textContent=p.items.length?`${p.items.length} сближений в ближайшие 30 дней. Ближайшая дата: ${p.items[0].date} (TDB).`:'В выбранном диапазоне сближений нет.';});}
function loadWeather(){load('weather',{},p=>{const list=$('weather-list');list.replaceChildren();for(const x of [...p.items].reverse()){const article=node('article',undefined,'flare');article.append(node('small','СОЛНЕЧНАЯ ВСПЫШКА'),node('b',x.class||'—'),node('p',stamp(x.date)));if(url(x.url))article.append(external('Запись DONKI ↗',x.url));list.append(article);}if(!p.items.length)list.append(node('div','За последние 7 дней в источнике нет зарегистрированных вспышек.','empty'));});}
function stopPlayback(){clearInterval(state.timer);state.timer=null;$('earth-play').textContent='▶ Воспроизвести';}
function showFrame(index){if(!state.frames.length)return;state.frame=index%state.frames.length;const p=state.frames[state.frame];$('earth-frame').src=url(p.image_url);$('earth-frame').hidden=false;$('earth-empty').hidden=true;$('earth-slider').value=state.frame;$('earth-time').textContent=p.date+' UTC';}
$('earth-frame').onerror=()=>{$('earth-empty').hidden=false;$('earth-empty').textContent='Этот кадр временно недоступен.';$('earth-frame').hidden=true;};
function loadEpic(){stopPlayback();load('epic',{collection:$('epic-collection').value,date:$('epic-date').value},p=>{state.frames=p.items;state.frame=0;$('earth-slider').max=Math.max(0,p.items.length-1);$('earth-slider').disabled=$('earth-play').disabled=!p.items.length;if(p.items.length)showFrame(0);else{$('earth-frame').hidden=true;$('earth-empty').hidden=false;$('earth-empty').textContent='За эту дату снимков нет. Выберите другую дату или последний доступный день.';$('earth-time').textContent='—';}});}
$('earth-play').onclick=()=>{if(state.timer){stopPlayback();return;}$('earth-play').textContent='Ⅱ Пауза';state.timer=setInterval(()=>showFrame(state.frame+1),900);};
$('earth-slider').oninput=e=>{stopPlayback();showFrame(Number(e.target.value));};
function initMap(){if(state.map)return;if(!window.L){$('map').replaceChildren(node('p','Не удалось загрузить карту. Список событий доступен ниже.','placeholder'));return;}state.map=L.map('map',{worldCopyJump:true}).setView([18,15],2);state.markers=L.layerGroup().addTo(state.map);updateTiles();}
function updateTiles(){if(!state.map)return;if(state.tiles)state.map.removeLayer(state.tiles);const d=$('map-date').value||yesterday;const tileURL=`https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/${d}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg`;state.tiles=L.tileLayer(tileURL,{maxNativeZoom:9,maxZoom:9,attribution:'NASA GIBS · Terra/MODIS'}).addTo(state.map);$('map-status').textContent=`Спутниковая съёмка: ${d} · NASA GIBS. Маркеры имеют собственные даты наблюдений. Покрытие может быть неполным.`;state.tiles.on('tileerror',()=>{$('map-status').textContent=`Часть снимков за ${d} недоступна. Попробуйте другую дату или уменьшите масштаб.`;});}
function position(g){if(g.type==='Point')return [g.coordinates[1],g.coordinates[0]];if(g.type==='Polygon'&&g.coordinates?.[0]?.[0])return [g.coordinates[0][0][1],g.coordinates[0][0][0]];return null;}
function renderEvents(){initMap();state.markers?.clearLayers();$('events-list').replaceChildren();const category=$('event-filter').value;const filtered=state.events.filter(e=>category==='all'||e.categories.some(c=>c.id===category));for(const event of filtered){const coordinates=position(event.geometry);const content=node('div');content.append(node('b',event.title),node('p',stamp(event.date)));if(url(event.url))content.append(external('Подробнее ↗',event.url));if(coordinates&&state.map)L.circleMarker(coordinates,{radius:6,color:'#e7be7d',fillColor:'#f4b469',fillOpacity:.8,weight:1}).bindPopup(content).addTo(state.markers);const card=node('button',undefined,'event');card.append(node('strong',event.title),node('small',event.categories.map(c=>c.title).join(', ')+' · '+stamp(event.date)));card.onclick=()=>{if(coordinates&&state.map){state.map.setView(coordinates,5);$('map').scrollIntoView({behavior:'smooth',block:'center'});}};$('events-list').append(card);}if(!filtered.length)$('events-list').append(node('div','Событий в этой категории нет.','empty'));}
function loadEvents(){load('events',{},p=>{state.events=p.items;const previous=$('event-filter').value;const categories=new Map();p.items.forEach(e=>e.categories.forEach(c=>categories.set(c.id,c.title)));$('event-filter').replaceChildren(new Option('Все категории','all'));categories.forEach((name,id)=>$('event-filter').add(new Option(name,id)));$('event-filter').value=categories.has(previous)?previous:'all';renderEvents();});}
function switchTab(tab){if(!$(tab)?.classList.contains('tab'))return;state.tab=tab;stopPlayback();document.querySelectorAll('.tab').forEach(e=>e.classList.toggle('active',e.id===tab));document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab));history.replaceState(null,'','#'+tab);if(tab==='overview'){loadAPOD();loadAsteroids();}if(tab==='rover')loadRover();if(tab==='media')loadMedia();if(tab==='earth'){loadEpic();initMap();state.map?.invalidateSize();loadEvents();}if(tab==='asteroids')loadAsteroids();if(tab==='weather')loadWeather();}
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>switchTab(b.dataset.tab));
$('rover-select').onchange=loadRover;$('epic-collection').onchange=loadEpic;$('epic-date').onchange=loadEpic;$('epic-latest').onclick=()=>{$('epic-date').value='';loadEpic();};
$('map-date').onchange=updateTiles;$('event-filter').onchange=renderEvents;$('map-world').onclick=()=>state.map?.setView([18,15],2);
$('search-form').onsubmit=e=>{e.preventDefault();state.media.collection='';state.media.page=1;renderCollections();loadMedia();};
switchTab(location.hash.slice(1)||'overview');
