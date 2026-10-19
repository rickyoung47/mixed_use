# 서울 토지이용 믹스

서울시 법정동 경계, 건축물 발자국, 도시지역 용도지역을 함께 탐색하는 정적 지도입니다. 건축물 데이터는 법정동 경계에 맞춰 PNG 지도 타일로 제공하고, 법정동과 용도지역은 지도에서 선택할 수 있는 GeoJSON 레이어로 제공합니다.

## 실행

정적 파일 서버로 `mixed_use` 폴더를 제공하면 됩니다. 예: `python3 -m http.server 8000`을 실행한 뒤 `http://localhost:8000`에서 확인합니다.

## 데이터 생성

원본 shapefile을 상위 `lecture05_Urban_Planning_Index/shp` 폴더에 둔 다음 아래 스크립트를 실행합니다.

```sh
python3 prepare_data.py
python3 render_building_tiles.py
```

Python 환경에는 GeoPandas, Shapely, Pillow, NumPy가 필요합니다. GeoJSON과 지도 타일은 서울 법정동 경계에 맞춰 잘라낸 웹 표시용 데이터입니다.

## 레이어와 색상

- 주거지역: 노랑
- 상업지역: 빨강
- 공업지역: 파랑
- 녹지지역: 초록
- 그 외: 연보라
- 건축물: 짙은 녹색 발자국
- 법정동: 점선 경계

지도는 원본 경계와 건축물 도형이 겹치는 법정동 영역만 표시합니다. 배경지도는 CARTO와 OpenStreetMap을 사용합니다.
