import folium
import folium.plugins
import pandas as pd
import streamlit as st
from pyproj import Geod
from streamlit_folium import st_folium

@st.cache_data
def load_data(url):
    df = pd.read_csv(url)
    df["navi"] = df.apply(lambda x: f'https://www.google.com/maps/dir/?api=1&destination={x["緯度"]},{x["経度"]}', axis=1)
    return df

st.set_page_config(page_title="いまばりAEDステーション")
st.title("いまばりAEDステーション")

my_map = "https://www.google.com/maps/d/edit?mid=18z3-aAlx_l3oYY1mM-OJwKo2TlJFXT0&usp=sharing"
st.write("[マイマップ](%s)" % my_map)

df0 = load_data(st.secrets["url"])

lat, lng = 34.0663183, 132.997528

# フォリウムマップの初期化
m = folium.Map(
    location=[lat, lng],
    tiles="https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png",
    attr='&copy; <a href="https://maps.gsi.go.jp/development/ichiran.html">国土地理院</a>',
    zoom_start=16,
)

# データフレームからマーカーを追加
for _, row in df0.iterrows():
    folium.Marker(
        location=[row["緯度"], row["経度"]],
        popup=folium.Popup(
            f'<a href={row["navi"]} target="_blank"><p>{row["タイトル"]}</p><p>{row["場所"]}</p></a>', max_width=300
        ),
        tooltip=row["タイトル"],
    ).add_to(m)

# 現在値
folium.plugins.LocateControl().add_to(m)

# マップをストリームリットに表示
st_data = st_folium(m, width=700, height=500)

# マップ境界内のデータフィルタリングと距離計算
if st_data:
    bounds = st_data["bounds"]
    center = st_data.get("center", {"lat": lat, "lng": lng})

    southWest_lat = bounds["_southWest"]["lat"]
    southWest_lng = bounds["_southWest"]["lng"]
    northEast_lat = bounds["_northEast"]["lat"]
    northEast_lng = bounds["_northEast"]["lng"]

    # 境界内のポイントをフィルタリング
    filtered_df = df0.loc[
        (df0["緯度"] >= southWest_lat)
        & (df0["緯度"] <= northEast_lat)
        & (df0["経度"] >= southWest_lng)
        & (df0["経度"] <= northEast_lng)
    ].copy()

    # 距離計算
    grs80 = Geod(ellps="GRS80")
    filtered_df["distance"] = filtered_df.apply(
        lambda row: grs80.inv(center["lng"], center["lat"], row["経度"], row["緯度"])[2], axis=1
    )

    # 距離でソート
    filtered_df.sort_values("distance", inplace=True)

    # 結果を表示
    df1 = filtered_df[["タイトル", "場所", "distance", "navi"]].head(10).reset_index(drop=True)
    st.dataframe(
        df1,
        width=700,
        column_config={
            "distance": "直線距離",
            "navi": st.column_config.LinkColumn("ナビ", display_text="🔗案内"),
        },
        hide_index=True,
    )
