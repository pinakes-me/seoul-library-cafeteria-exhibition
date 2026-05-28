"""
make_comparison_map.py
========================
서울시 공공도서관 구내식당 분포 비교 지도 (2019 ↔ 2025)

libraries_2019_2025.csv를 읽어, 연도별 구내식당 보유 현황을
folium 지도 위에 마커로 표시한다. 라디오 버튼으로 2019/2025를
전환할 수 있으며, 첫 로딩 시 2019년 레이어가 선택된다.

- 입력: data/libraries_2019_2025.csv
- 출력: libraries_2019_2025_comparison.html  (전시의 Map 01)

실행 방법:
    pip install folium
    python make_comparison_map.py
"""

import csv
import folium

CSV_PATH = "data/libraries_2019_2025.csv"
OUTPUT_PATH = "libraries_2019_2025_comparison.html"
SEOUL_CENTER = [37.5665, 126.9780]


def load_libraries(csv_path):
    """CSV를 읽어 도서관 목록을 딕셔너리 리스트로 반환한다."""
    libraries = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            libraries.append({
                "name": row["name"],
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
                "2019_has_cafeteria": row["2019_has_cafeteria"].strip().lower(),
                "2025_has_cafeteria": row["2025_has_cafeteria"].strip().lower(),
                "url": row.get("url", "#"),
                "etc": row.get("etc", ""),
            })
    return libraries


def build_popup_html(name, year, has_cafeteria, url, etc):
    """마커 클릭 시 뜨는 팝업 HTML을 생성한다."""
    cafeteria_badge = (
        '<span style="color:blue">있음 ⭕</span>'
        if has_cafeteria == "yes"
        else '<span style="color:red">없음 ❌</span>'
    )
    etc_text = (
        f"<br><small style='color:gray'>{etc}</small>" if etc.strip() else ""
    )
    return f"""
    <div style="font-size: 12px; font-family: 'Noto Sans KR', sans-serif; min-width:150px;">
        <strong style="font-size: 14px; color:#2a5db0;">{name} ({year})</strong><br>
        🍽 구내식당: {cafeteria_badge}<br>
        <a href="{url}" target="_blank">홈페이지 바로가기</a>{etc_text}
    </div>
    """


def add_year_markers(layer, libraries, year_key, year_label):
    """특정 연도의 구내식당 데이터가 있는 도서관 마커를 레이어에 추가한다."""
    for lib in libraries:
        has_cafeteria = lib[year_key]

        # 해당 연도 데이터가 비어있으면(존재하지 않으면) 건너뛴다
        if len(has_cafeteria) == 0:
            continue

        icon_name = "cutlery" if has_cafeteria == "yes" else "info"
        color = "orange" if has_cafeteria == "yes" else "gray"

        popup_html = build_popup_html(
            lib["name"], year_label, has_cafeteria, lib["url"], lib["etc"]
        )

        folium.Marker(
            location=[lib["lat"], lib["lon"]],
            icon=folium.Icon(icon=icon_name, prefix="fa", color=color),
            popup=folium.Popup(popup_html, max_width=250),
        ).add_to(layer)


def main():
    libraries = load_libraries(CSV_PATH)
    m = folium.Map(location=SEOUL_CENTER, zoom_start=11)

    # 연도별 레이어 (overlay=False → 라디오 버튼: 한 번에 하나만 선택)
    layer_2019 = folium.FeatureGroup(name="🍽️ 2019년 도서관 구내식당 현황", overlay=False)
    layer_2025 = folium.FeatureGroup(name="🍽️ 2025년 도서관 구내식당 현황", overlay=False)

    folium.TileLayer("openstreetmap", name="2019 배경").add_to(layer_2019)
    folium.TileLayer("openstreetmap", name="2025 배경").add_to(layer_2025)

    add_year_markers(layer_2019, libraries, "2019_has_cafeteria", "2019")
    add_year_markers(layer_2025, libraries, "2025_has_cafeteria", "2025")

    # 추가 순서가 라디오 버튼 목록 순서를 결정한다 (2019가 위)
    layer_2019.add_to(m)
    layer_2025.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    # 첫 로딩 시 2019 레이어를 자동 선택 (컨트롤 생성 후 실행되도록 약간 지연)
    auto_click_script = """
    <script>
    window.onload = function() {
        setTimeout(function() {
            var radioButtons = document.querySelectorAll('input[type="radio"].leaflet-control-layers-selector');
            if (radioButtons.length > 0) {
                radioButtons[1].click();
            }
        }, 100);
    };
    </script>
    """
    m.get_root().html.add_child(folium.Element(auto_click_script))

    style = """
    <style>
    .leaflet-control-layers { font-size: 12px !important; font-family: 'Noto Sans KR', sans-serif !important; }
    </style>
    """
    m.get_root().html.add_child(folium.Element(style))

    legend_html = """
    <div style="
        position: fixed; bottom: 20px; right: 20px; width: 160px;
        background-color: white; border:2px solid grey; z-index:9999;
        font-size:12px; padding: 10px;">
    <b>📌 구내식당 보유 여부</b><br><br>
    <span style="color:orange;">🟠</span> 식당 있는 도서관 ⭕️<br>
    <span style="color:gray;">⚫️</span> 식당 없는 도서관 ❌
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    m.save(OUTPUT_PATH)
    print(f"완료: {OUTPUT_PATH} 생성 (2019년이 기본으로 선택됩니다)")


if __name__ == "__main__":
    main()
