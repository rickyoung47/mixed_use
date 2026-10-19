const colors = { '주거지역': '#e6c642', '상업지역': '#df6a5c', '공업지역': '#5593c2', '녹지지역': '#72a27a', '그 외': '#ae9cca' };
const map = L.map('map', { zoomControl: false, preferCanvas: true, zoomSnap: 0.25, minZoom: 10, maxZoom: 19, attributionControl: true });
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png', { subdomains: 'abcd', maxZoom: 20, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>' }).addTo(map);
const esc = (value) => String(value ?? '정보 없음').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const setCount = (id, value) => document.getElementById(id).textContent = Number(value).toLocaleString('ko-KR');
const loading = document.getElementById('loading');
const layerConfigs = [
  { file: 'landuse', id: 'toggleLand', pane: 'landuse', style: f => ({ color: '#fffdf5', weight: 0.45, opacity: 0.72, fillColor: colors[f.properties.zone] || colors['그 외'], fillOpacity: 0.78 }), popup: f => `<b>${esc(f.properties.DGM_NM)}</b><br><span class="popup-muted">${esc(f.properties.zone)}</span>` },
  { file: 'dong', id: 'toggleDong', pane: 'dong', style: () => ({ color: '#263f33', weight: 1.25, opacity: 0.9, fillColor: '#758b76', fillOpacity: 0.035, dashArray: '5 3' }), popup: f => `<b>${esc(f.properties.EMD_NM)}</b><br><span class="popup-muted">법정동 코드 ${esc(f.properties.EMD_CD)}</span>` }
];
map.createPane('landuse').style.zIndex = 410;
map.createPane('buildings').style.zIndex = 420;
map.createPane('dong').style.zIndex = 430;
const layers = {};
Promise.all(layerConfigs.map(async config => {
  const response = await fetch(`data/${config.file}.geojson`);
  if (!response.ok) throw new Error(`${config.file}: ${response.status}`);
  const data = await response.json();
  setCount(config.file === 'landuse' ? 'zoneCount' : 'dongCount', data.features.length);
  const layer = L.geoJSON(data, { pane: config.pane, style: config.style, onEachFeature: (feature, item) => item.bindPopup(config.popup(feature), { className: 'feature-popup', maxWidth: 250 }) });
  layers[config.id] = layer;
  if (document.getElementById(config.id).checked) layer.addTo(map);
  return { config, layer };
})).then(results => {
  fetch('data/summary.json').then(r => r.json()).then(summary => setCount('buildingCount', summary.buildings));
  const buildings = L.tileLayer('tiles/buildings/{z}/{x}/{y}.png', { pane: 'buildings', minZoom: 10, maxZoom: 17, maxNativeZoom: 17, opacity: 1, tileSize: 256, keepBuffer: 3, updateWhenIdle: true });
  layers.toggleBuildings = buildings;
  if (document.getElementById('toggleBuildings').checked) buildings.addTo(map);
  const bounds = results.find(x => x.config.file === 'dong').layer.getBounds();
  map.fitBounds(bounds, { paddingTopLeft: [45, 35], paddingBottomRight: [260, 35], maxZoom: 13.5 });
  loading.classList.add('hidden');
}).catch(error => {
  console.error(error);
  loading.innerHTML = '<b>지도를 불러오지 못했어요</b><small>새로고침 후 다시 확인해 주세요.</small>';
});
layerConfigs.forEach(({ id }) => document.getElementById(id).addEventListener('change', event => {
  if (event.target.checked) layers[id]?.addTo(map); else if (layers[id]) map.removeLayer(layers[id]);
  event.target.closest('.layer-row').querySelector('.layer-state').textContent = event.target.checked ? 'ON' : 'OFF';
}));
document.getElementById('toggleBuildings').addEventListener('change', event => {
  if (event.target.checked) layers.toggleBuildings?.addTo(map); else if (layers.toggleBuildings) map.removeLayer(layers.toggleBuildings);
  event.target.closest('.layer-row').querySelector('.layer-state').textContent = event.target.checked ? 'ON' : 'OFF';
});
document.getElementById('zoomAll').addEventListener('click', () => { const layer = layers.toggleDong; if (layer) map.fitBounds(layer.getBounds(), { paddingTopLeft: [45, 35], paddingBottomRight: [260, 35], maxZoom: 13.5 }); });
document.getElementById('locate').addEventListener('click', () => { const layer = layers.toggleDong; if (layer) map.fitBounds(layer.getBounds(), { paddingTopLeft: [45, 35], paddingBottomRight: [260, 35], maxZoom: 13.5 }); });
const dialog = document.getElementById('aboutDialog');
document.getElementById('aboutButton').addEventListener('click', () => dialog.showModal());
document.getElementById('closeDialog').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
