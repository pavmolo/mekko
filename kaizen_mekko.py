import streamlit as st
import numpy as np
import plotly.graph_objs as go
import pandas as pd
import html

# Функция для расчета размера шрифта в блоках диаграммы
def calculate_font_size(width_percent, height_percent, text_length):
    graph_width_px = 800
    graph_height_px = 600
    block_width_px = width_percent * graph_width_px / 100
    block_height_px = height_percent * graph_height_px / 100
    char_width = 8
    char_height = 12
    font_size_by_width = block_width_px / (text_length * char_width) * 12 * 0.5
    font_size_by_height = block_height_px / char_height * 12 * 0.8
    return max(8, min(font_size_by_width, font_size_by_height))

# Функция для анализа позиции на рынке
def analyze_market_position(data_df):
    market_names = data_df.columns[1:].tolist()
    company_names = data_df.iloc[1:, 0].tolist()
    our_company_name = data_df.iloc[1, 0]
    
    market_positions = {}
    market_characteristics = {}
    recommendations = {}
    leaders = {}
    our_market_shares = {}

    for idx, market in enumerate(market_names):
        our_share = data_df.loc[data_df.iloc[:, 0] == our_company_name, market].values[0]
        all_shares = data_df.iloc[1:, idx+1].values
        max_share = max(all_shares)
        leader_idx = np.argmax(all_shares)
        leader_company = company_names[leader_idx]

        our_market_shares[market] = f"{our_share*100:.2f}%"

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

        if len([share for share in all_shares if share > 0.1]) > 3:
            market_characteristics[market] = "Высококонкурентный"
        elif max_share > 0.5:
            market_characteristics[market] = "Олигополистический"
        else:
            market_characteristics[market] = "Раздробленный"

        leaders[market] = leader_company

    return our_company_name, our_market_shares, market_positions, market_characteristics, recommendations, leaders

# Streamlit приложение
st.title("Mekko Chart App")

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

    cumulative_percentages = np.cumsum(widths) / widths.sum() * widths.sum()
    percent_labels = [f"{label} ({int(width)}%)" for label, width in zip(labels, widths / widths.sum() * 100)]
        
    fig.update_xaxes(
        tickvals=cumulative_percentages - (np.array(widths) / widths.sum() * widths.sum() / 2),
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

    our_company_name, our_market_shares, market_positions, market_characteristics, recommendations, leaders = analyze_market_position(data_df)
    # Описания характеристик рынка
    market_characteristics_descriptions = {
        "Высококонкурентный": "Рынок, на котором множество компаний имеют схожую долю рынка.",
        "Олигополистический": "Рынок, на котором одна или несколько компаний контролируют большую часть рынка.",
        "Раздробленный": "Рынок, на котором множество мелких игроков, но нет явного лидера."
    }
    
    # Описания рекомендаций
    recommendations_descriptions = {
        "Отсутствует": "Ваша компания отсутствует на данном рынке. Это может быть связано с отсутствием интереса к данному сегменту или недостаточной информацией. Рассмотрите возможность исследования этого рынка для определения потенциальных возможностей.",
        "Маленький игрок": "Ваша компания имеет небольшую долю на данном рынке. Это может быть связано с недавним входом на рынок или с конкурентной борьбой. Рассмотрите стратегии для увеличения вашей доли, такие как маркетинговые кампании или партнерства.",
        "Конкурент": "Ваша компания является одним из ключевых игроков на рынке, но не доминирует. Это может требовать усиленных усилий для удержания вашей позиции и противостояния конкурентам. Рассмотрите стратегии для увеличения вашей доли или удержания текущей позиции.",
        "Лидер": "Ваша компания доминирует на данном рынке. Это отличная позиция, но требует постоянного внимания к изменениям на рынке и потребностям клиентов. Сосредоточьтесь на удержании лидирующей позиции и исследуйте новые возможности для роста."
    }
    st.write(f"Анализ для компании: **{our_company_name}**")
    
    for market in market_positions:
        st.header(f"Рынок {market}:")
        
        st.markdown(f"**Ваше положение:** {market_positions.get(market, 'Не определено')}")
        st.markdown(f"**Лидер на рынке:** {leaders.get(market, 'Не определено')}")
        
        market_characteristic_description = html.escape(market_characteristics_descriptions.get(market_characteristics.get(market, 'Не определено'), ''))
        recommendation_description = html.escape(recommendations_descriptions.get(recommendations.get(market, 'Не определено'), ''))
        
        st.markdown(f"**Характеристика рынка:** {market_characteristics.get(market, 'Не определено')}{' - ' + market_characteristic_description if market_characteristic_description else ''}")
        st.markdown(f"**Рекомендация:** {recommendations.get(market, 'Не определено')} - {recommendation_description}")
        
        st.divider()
