"""
make_facility_map.py
=====================
서울시 공공도서관 편의시설(구내식당·카페) 분포 지도 — 운영 주체별 (2025년 기준)

libraries_2019_2025.csv를 읽어, 2025년 시점의 식당·카페 보유 현황을
folium 지도 위에 색상으로 구분해 표시한다. 운영 주체(자치구/교육청/기타)별로
레이어를 나누어 토글할 수 있다.

마커 색상:
  🟠 식당만  🟢 카페만  🔵 식당+카페 모두  ⚫️ 둘 다 없음

- 입력: data/libraries_2019_2025.csv
- 출력: libraries_facility_2025_by_owner.html  (전시의 Map 02)

실행 방법:
    pip install folium
    python make_facility_map.py
"""

import csv
import folium

CSV_PATH = "data/libraries_2019_2025.csv"
OUTPUT_PATH = "libraries_facility_2025_by_owner.html"
SEOUL_CENTER = [37.5665, 126.9780]


def load_libraries(csv_path):
    """CSV를 읽어, 2025년 데이터가 존재하는 도서관만 목록으로 반환한다."""
    libraries = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_cafeteria = row["2025_has_cafeteria"].strip().lower()

            # 2025년 구내식당 데이터가 존재하는 경우에만 포함
            if len(raw_cafeteria) == 0:
                continue

            libraries.append({
                "name": row["name"],
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
                "has_cafe": row["has_cafe"].strip().lower() == "yes",
                "has_cafeteria": raw_cafeteria == "yes",
                "owned_by": row["owned_by"],
                "url": row.get("url", "#"),
                "etc": row.get("etc", ""),
            })
    return libraries


def pick_icon_and_color(has_cafeteria, has_cafe):
    """식당·카페 보유 조합에 따라 (아이콘, 색상)을 결정한다."""
    if has_cafeteria and has_cafe:
        return "cutlery", "blue"     # 식당 + 카페 모두
    elif has_cafeteria:
        return "cutlery", "orange"   # 식당만
    elif has_cafe:
        return "coffee", "green"     # 카페만
    else:
        return "info", "gray"        # 둘 다 없음


def build_popup_html(lib):
    """마커 클릭 시 뜨는 팝업 HTML을 생성한다."""
    cafe_badge = (
        '<span style="color:green">⭕️</span>' if lib["has_cafe"]
        else '<span style="color:red">❌</span>'
    )
    cafeteria_badge = (
        '<span style="color:orange">⭕️</span>' if lib["has_cafeteria"]
        else '<span style="color:red">❌</span>'
    )
    etc_text = (
        f"<br><small style='color:gray'>{lib['etc']}</small>"
        if lib["etc"].strip() else ""
    )
    # 도서관 이름을 홈페이지 링크로 연결 (원본의 깨진 태그를 수정)
    return f"""
    <div style="font-size: 12px; font-family: 'Noto Sans KR', sans-serif;">
        <strong style="font-size: 14px;">
            <a href="{lib['url']}" target="_blank" style="text-decoration:none; color:#2a5db0;">{lib['name']}</a>
        </strong><br>
        ☕ 카페: {cafe_badge}<br>
        🍽 식당: {cafeteria_badge}<br>
        <a href="{lib['url']}" target="_blank">홈페이지 바로가기</a>{etc_text}
    </div>
    """


def main():
    libraries = load_libraries(CSV_PATH)
    m = folium.Map(location=SEOUL_CENTER, zoom_start=11)

    # 운영 주체별 레이어
    district_layer = folium.FeatureGroup("🏛 서울시·자치구 도서관")
    edu_layer = folium.FeatureGroup("🏫 서울시교육청 도서관")
    etc_layer = folium.FeatureGroup("🏢 사립 등 기타")

    for lib in libraries:
        icon_name, color = pick_icon_and_color(lib["has_cafeteria"], lib["has_cafe"])
        popup_html = build_popup_html(lib)

        marker = folium.Marker(
            location=[lib["lat"], lib["lon"]],
            icon=folium.Icon(icon=icon_name, prefix="fa", color=color),
            popup=folium.Popup(popup_html, max_width=250),
        )

        if lib["owned_by"] == "자치구":
            marker.add_to(district_layer)
        elif lib["owned_by"] == "교육청":
            marker.add_to(edu_layer)
        else:
            marker.add_to(etc_layer)

    district_layer.add_to(m)
    edu_layer.add_to(m)
    etc_layer.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    style = """
    <style>
    .leaflet-control-layers { font-size: 13px !important; padding: 8px !important; }
    .leaflet-control-layers label { font-size: 13px !important; }
    </style>
    """
    m.get_root().html.add_child(folium.Element(style))

    legend_html = """
    <div style="
        position: fixed; bottom: 20px; right: 20px; width: 200px;
        background-color: white; border:2px solid grey; z-index:9999;
        font-size:12px; padding: 10px;">
    <b>📌 구내식당 및 카페 보유 여부</b><br><br>
    <span style="color:orange;">🟠</span> 식당 있는 도서관<br>
    <span style="color:green;">🟢</span> 카페 있는 도서관<br>
    <span style="color:blue;">🔵</span> 식당+카페 모두 있음<br>
    <span style="color:gray;">⚫️</span> 식당·카페 모두 없음
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    m.save(OUTPUT_PATH)
    print(f"완료: {OUTPUT_PATH} 생성")


if __name__ == "__main__":
    main()
