import streamlit as st
import numpy as np
import plotly.graph_objs as go
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns


st.markdown(
    '<div style="text-align:center;"><img src="https://i.ibb.co/bXgXp1C/photo-5472038646254260855-c.jpg" style="width:15%; margin-bottom:30px;"></div>', 
    unsafe_allow_html=True
)
def calculate_font_size(width_percent, height_percent, text_length):
    graph_width_px = 800
    graph_height_px = 600
    block_width_px = width_percent * graph_width_px / 100
    block_height_px = height_percent * graph_height_px / 100
    char_width = 8
    char_height = 12
    font_size_by_width = block_width_px / (text_length * char_width) * 12 * 0.5  # уменьшено на 20%
    font_size_by_height = block_height_px / char_height * 12 * 0.8  # уменьшено на 20%
    return max(8, min(font_size_by_width, font_size_by_height))

def analyze_market_position(data_df):
    market_names = data_df.columns[1:].tolist()
    market_sizes = data_df.iloc[0, 1:].values
    company_names = data_df.iloc[1:, 0].tolist()  # Изменено здесь
    our_company_name = data_df.iloc[1, 0]
    
    market_positions = {}
    market_characteristics = {}
    recommendations = {}
    leaders = {}
    our_market_shares = {}

    for idx, market in enumerate(market_names):
        our_share = data_df.loc[data_df.iloc[:, 0] == our_company_name, market].values[0]
        all_shares = data_df.iloc[1:, idx+1].values  # Изменено здесь
        max_share = max(all_shares)
        leader_idx = np.argmax(all_shares)  # Изменено здесь
        leader_company = company_names[leader_idx]

        # Запись доли рынка нашей компании
        our_market_shares[market] = f"{our_share*100:.2f}%"

        # Определение позиции на рынке
        if our_share == 0:
            market_positions[market] = "Отсутствует"
            recommendations[market] = "Рассмотрите возможность входа на рынок"
        elif our_share < 0.1:
            market_positions[market] = "Маленький игрок"
            recommendations[market] = "Рассмотрите стратегии для увеличения доли"
        elif our_share < max_share:
            market_positions[market] = "Конкурент"
            recommendations[market] = "Рассмотрите стратегии для увеличения доли или удержания текущей позиции"
        else:
            market_positions[market] = "Лидер"
            recommendations[market] = "Сосредоточьтесь на удержании лидирующей позиции"

        # Определение характеристики рынка
        if len([share for share in all_shares if share > 0.1]) > 3:
            market_characteristics[market] = "Высококонкурентный"
        elif max_share > 0.5:
            market_characteristics[market] = "Олигополистический"
        else:
            market_characteristics[market] = "Раздробленный"

        # Определение лидера на рынке
        leaders[market] = leader_company

    return our_company_name, our_market_shares, market_positions, market_characteristics, recommendations, leaders



st.title("Mekko Chart App")
with st.expander("Инструкция по созданию эксель файла"):
    st.markdown(
        '<div style="text-align:center;"><img src="https://i.ibb.co/t8z0qgN/2023-09-28-13-11-25.png"></div>', 
        unsafe_allow_html=True
    )

uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

if uploaded_file:
    data_df = pd.read_excel(uploaded_file, engine='openpyxl')
    columns = list(data_df.columns)[1:]
    labels = columns
    widths = data_df.iloc[0, 1:].values.astype(float)
    data_df = data_df.drop(0)
    data_percentage = data_df.copy()
    for col in columns:
        data_percentage[col] = data_df[col] / data_df[col].sum()
    data = data_percentage.set_index(data_df.columns[0]).T.to_dict()

    fig = go.Figure()
    annotations = []
    cumulative_y = [0] * len(labels)

    for key in data:
        fig.add_trace(go.Bar(
            name=key,
            y=list(data[key].values()),
            x=np.cumsum(widths)-widths,
            width=widths,
            offset=0,
            customdata=np.transpose([labels, widths*np.array(list(data[key].values()))])
        ))
        
        for i, (x_val, y_val, width_val) in enumerate(zip(np.cumsum(widths)-widths, data[key].values(), widths)):
            if y_val > 0:
                font_size = calculate_font_size(width_val, y_val*100, len(f"{key}: {y_val*100:.0f}%"))
                annotations.append(
                    dict(
                        x=x_val + width_val/2,
                        y=cumulative_y[i] + y_val/2,
                        xref='x',
                        yref='y',
                        text=f"{key}: {y_val*100:.0f}%",
                        showarrow=False,
                        font=dict(color="white", size=font_size),
                        align="center"
                    )
                )
            cumulative_y[i] += y_val

    cumulative_percentages = np.cumsum(widths) / widths.sum() * widths.sum()  # Изменено здесь
    percent_labels = [f"{label} ({int(width)}%)" for label, width in zip(labels, widths / widths.sum() * 100)]
        
    fig.update_xaxes(
        tickvals=cumulative_percentages - (np.array(widths) / widths.sum() * widths.sum() / 2),  # Изменено здесь
        ticktext=percent_labels
    )
    fig.update_xaxes(tickformat=".0%", range=[0, widths.sum()])
    fig.update_yaxes(tickformat=".0%", range=[0, 1], side="left", showgrid=False)
    fig.update_layout(
        title_text="Mekko Chart",
        barmode="stack",
        uniformtext=dict(mode="hide", minsize=10),
        annotations=annotations,
        bargap=0.05,
        margin=dict(l=10),
        showlegend=False
    )
    for trace in fig.data:
        trace.marker.line.width = 2
        trace.marker.line.color = "white"
    st.plotly_chart(fig)

    data_df = pd.read_excel(uploaded_file, engine='openpyxl')
    our_company_name, our_market_shares, market_positions, market_characteristics, recommendations, leaders = analyze_market_position(data_df)
    # Вывод названия вашей компании
    #st.write(f"Анализ для компании: **{our_company_name}**")
    
    for market in market_positions:
        st.header(f"Рынок {market}:")
        st.write(f"Ваше положение: {market_positions.get(market, 'Не определено')}")
        st.write(f"Лидер на рынке: {leaders.get(market, 'Не определено')}")
        st.write(f"Характеристика рынка: {market_characteristics.get(market, 'Не определено')}")
        st.write(f"Рекомендация: {recommendations.get(market, 'Не определено')}")
        st.divider()
