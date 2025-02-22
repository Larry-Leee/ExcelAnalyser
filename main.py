import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np


def is_numeric_column(series):
    """检查列是否为数值类型"""
    return pd.api.types.is_numeric_dtype(series) or all(pd.to_numeric(series, errors='coerce').notna())


def load_data(file):
    """读取Excel文件并进行基础验证"""
    try:
        df = pd.read_excel(file)

        # 获取数值类型的列cd
        numeric_cols = []
        text_cols = []

        for col in df.columns:
            if is_numeric_column(df[col]):
                numeric_cols.append(col)
            else:
                text_cols.append(col)

        if not numeric_cols:
            st.error("未找到数值类型的列，请检查Excel文件格式")
            return None, [], []

        # 确保数值列都转换为float类型
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        return df, numeric_cols, text_cols
    except Exception as e:
        st.error(f"读取文件出错: {str(e)}")
        return None, [], []


def create_trend_chart(df, name_col, plan_col, actual_col):
    """创建整体趋势图"""
    fig = go.Figure()

    # 添加计划线
    fig.add_trace(
        go.Scatter(x=df[name_col], y=df[plan_col],
                   name='计划值',
                   line=dict(color='rgb(31, 119, 180)'),
                   mode='lines+markers')
    )

    # 添加实际线
    fig.add_trace(
        go.Scatter(x=df[name_col], y=df[actual_col],
                   name='实际值',
                   line=dict(color='rgb(255, 99, 71)'),
                   mode='lines+markers')
    )

    fig.update_layout(
        title='计划值 vs 实际值趋势图',
        xaxis_title='掌子面位置',
        yaxis_title='数值',
        hovermode='x unified',
        xaxis=dict(
            tickangle=45,
            tickmode='array',
            ticktext=df[name_col].tolist(),
            tickvals=df[name_col].tolist(),
            dtick = 2
        ),
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )

    return fig


def create_variance_chart(df, name_col, variance_col):
    """创建差异分析图"""
    colors = ['red' if x < 0 else 'green' for x in df[variance_col]]

    fig = go.Figure()

    # 添加差异柱状图
    fig.add_trace(
        go.Bar(x=df[name_col].tolist(),
               y=df[variance_col].tolist(),
               name='差异值',
               marker_color=colors,
               text=df[variance_col].round(2).tolist(),
               textposition='outside')
    )

    fig.update_layout(
        title='差异分析图',
        xaxis_title='掌子面位置',
        yaxis_title='差异值',
        hovermode='x unified',
        xaxis=dict(
            tickangle=45,
            tickmode='array',
            ticktext=df[name_col].tolist(),
            tickvals=df[name_col].tolist(),
            dtick = 2
        ),
        showlegend=True
    )

    # 添加零线
    fig.add_hline(y=0, line_dash="dash", line_color="gray")

    return fig


def main():
    st.title('掌子面进度分析与可视化工具')

    # 文件上传
    uploaded_file = st.file_uploader("请选择Excel文件", type=['xlsx', 'xls'])

    if uploaded_file is not None:
        # 读取数据
        df, numeric_cols, text_cols = load_data(uploaded_file)

        if df is not None and numeric_cols:
            # 显示原始数据
            st.subheader('原始数据')
            st.dataframe(df)

            # 选择列
            st.write("请选择要分析的数据列：")
            name_col = st.selectbox('选择掌子面名称列', text_cols)
            plan_col = st.selectbox('选择计划值列', numeric_cols)
            actual_col = st.selectbox('选择实际值列', numeric_cols)
            df = df[~df[plan_col].isin([0, '/'])]

            if name_col and plan_col and actual_col:
                try:
                    # 数据预处理
                    df['差异值'] = df[actual_col] - df[plan_col]
                    df['差异率'] = np.where(df[plan_col] != 0,
                                         (df['差异值'] / df[plan_col]) * 100,
                                         0)

                    # 显示统计指标
                    st.subheader('统计分析')
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        completion_rate = (df[actual_col].sum() / df[plan_col].sum() * 100) if df[
                                                                                                   plan_col].sum() != 0 else 0
                        avg_completion_rate = (df[actual_col].mean() / df[plan_col].mean() * 100) if df[
                                                                                                         plan_col].mean() != 0 else 0
                        st.metric('总体完成率', f"{completion_rate:.2f}%")
                        st.metric('平均完成率', f"{avg_completion_rate:.2f}%")

                    with col2:
                        st.metric('超计划掌子面数量', int(len(df[df['差异值'] > 0])))
                        st.metric('未达计划掌子面数量', int(len(df[df['差异值'] < 0])))

                    with col3:
                        st.metric('最大超计划值', f"{df['差异值'].max():.2f}")
                        st.metric('最大滞后值', f"{df['差异值'].min():.2f}")

                    # 显示趋势图
                    st.subheader('趋势分析')
                    trend_fig = create_trend_chart(df, name_col, plan_col, actual_col)
                    st.plotly_chart(trend_fig, use_container_width=True)

                    # 显示差异分析图
                    st.subheader('差异分析')
                    variance_fig = create_variance_chart(df, name_col, '差异值')
                    st.plotly_chart(variance_fig, use_container_width=True)

                    # 显示详细数据
                    st.subheader('差异详细数据')
                    detailed_df = df[[name_col, plan_col, actual_col, '差异值', '差异率']]

                    # 设置样式和格式
                    styled_df = detailed_df.style.format({
                        plan_col: '{:.2f}',
                        actual_col: '{:.2f}',
                        '差异值': '{:.2f}',
                        '差异率': '{:.2f}%'
                    }).apply(lambda x: ['background-color: rgba(255,0,0,0.2)' if v < 0
                                        else 'background-color: rgba(0,255,0,0.2)'
                                        for v in x['差异值']], axis=1)

                    st.dataframe(styled_df)

                    # 添加数据下载按钮
                    csv = detailed_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="下载分析数据",
                        data=csv,
                        file_name="掌子面分析数据.csv",
                        mime="text/csv"
                    )

                except Exception as e:
                    st.error(f"处理数据时出错: {str(e)}")
                    st.write("请检查数据格式是否正确")


if __name__ == '__main__':
    main()