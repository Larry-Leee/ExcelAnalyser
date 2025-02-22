import pandas as pd
import numpy as np
from pyecharts import options as opts
from pyecharts.charts import Line, Bar
from pyecharts.globals import ThemeType
import streamlit as st
import streamlit.components.v1 as components
import tempfile


def load_excel(file_path):
    """读取Excel文件"""
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        st.error(f"读取文件出错: {str(e)}")
        return None


def calculate_variance(planned, actual):
    """计算计划值和实际值的差异"""
    variance = actual - planned
    variance_pct = (variance / planned) * 100
    return variance, variance_pct


def create_comparison_chart(df, face_name_column, plan_column, actual_column):
    """创建计划值vs实际值对比图"""
    line = (
        Line(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="1000px", height="600px"))  # 调整图表宽度和高度
        .add_xaxis(df[face_name_column].tolist())
        .add_yaxis("计划值", df[plan_column].tolist(),
                   symbol_size=8, is_symbol_show=True, color='blue')
        .add_yaxis("实际值", df[actual_column].tolist(),
                   symbol_size=8, is_symbol_show=True, color='green')
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="计划vs实际对比图",
                title_textstyle_opts=opts.TextStyleOpts(font_size=18, font_weight='bold', color='black')
            ),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            xaxis_opts=opts.AxisOpts(
                type_="category",
                name="掌子面名称",
                name_location="middle",
                name_gap=30,
                axislabel_opts=opts.LabelOpts(
                    rotate=45,  # 旋转x轴标签45度，避免重叠
                    interval=0  # 确保显示所有标签
                )
            ),
            yaxis_opts=opts.AxisOpts(type_="value", name="数值", name_location="middle", name_gap=40),
            legend_opts=opts.LegendOpts(pos_top="5%", pos_left="center"),
            toolbox_opts=opts.ToolboxOpts(is_show=True, orient="horizontal", pos_top="10%")
        )
    )
    return line


def create_variance_chart(df, face_name_column, variance_column):
    """创建差异分析图"""
    bar = (
        Bar(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="1000px", height="600px"))  # 调整图表宽度和高度
        .add_xaxis(df[face_name_column].tolist())
        .add_yaxis("差异值", df[variance_column].tolist(),
                   label_opts=opts.LabelOpts(position="top"))
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="计划vs实际差异分析",
                title_textstyle_opts=opts.TextStyleOpts(font_size=18, font_weight='bold', color='black')
            ),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            xaxis_opts=opts.AxisOpts(
                type_="category",
                name="掌子面名称",
                name_location="middle",
                name_gap=30,
                axislabel_opts=opts.LabelOpts(
                    rotate=45,  # 旋转x轴标签45度，避免重叠
                    interval=0  # 确保显示所有标签
                )
            ),
            yaxis_opts=opts.AxisOpts(type_="value", name="差异值", name_location="middle", name_gap=40),
            legend_opts=opts.LegendOpts(pos_top="5%", pos_left="center"),
            toolbox_opts=opts.ToolboxOpts(is_show=True, orient="horizontal", pos_top="10%")
        )
    )
    return bar


def analyze_comparison(df, plan_column, actual_column):
    """分析计划值和实际值的对比"""
    analysis = {
        "计划平均值": df[plan_column].mean(),
        "实际平均值": df[actual_column].mean(),
        "计划最大值": df[plan_column].max(),
        "实际最大值": df[actual_column].max(),
        "计划最小值": df[plan_column].min(),
        "实际最小值": df[actual_column].min(),
        "总体完成率": (df[actual_column].sum() / df[plan_column].sum()) * 100,
        "超计划次数": len(df[df[actual_column] > df[plan_column]]),
        "未达计划次数": len(df[df[actual_column] < df[plan_column]])
    }
    return analysis


def highlight(val):
    """定义高亮函数"""
    color = 'green' if val > 0 else 'red'
    return f'color: {color}'


def main():
    # 设置页面背景颜色为白色
    st.markdown("""
        <style>
        .reportview-container {
            background-color: white;
        }
        .block-container {
            padding: 2rem;
        }
        </style>
        """, unsafe_allow_html=True)

    st.title("计划vs实际数据分析与可视化")

    # 文件上传
    uploaded_file = st.file_uploader("请选择Excel文件", type=["xlsx", "xls"])

    if uploaded_file is not None:
        # 读取数据
        df = load_excel(uploaded_file)

        if df is not None:
            # 显示原始数据

            st.subheader("原始数据")
            st.dataframe(df)

            # 选择掌子面名称列
            face_name_columns = df.select_dtypes(include=['object']).columns
            if '掌子面名称' in face_name_columns:
                face_name_column = '掌子面名称'  # 假设掌子面名称列已经存在
            else:
                st.error("未找到掌子面名称列，请确保Excel中包含掌子面名称数据")
                return

            # 选择计划值和实际值的列
            numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
            plan_column = st.selectbox("选择计划值列", numeric_columns)
            actual_column = st.selectbox("选择实际值列", numeric_columns)
            df = df[~df[plan_column].isin([0, '/'])]

            # 按照掌子面名称排序数据
            df_sorted = df.sort_values(by=face_name_column)

            # 计算差异
            df_sorted['差异值'] = df_sorted[actual_column] - df_sorted[plan_column]
            df_sorted['差异百分比'] = (df_sorted['差异值'] / df_sorted[plan_column]) * 100

            # 显示对比分析结果
            st.subheader("对比分析")
            analysis_results = analyze_comparison(df_sorted, plan_column, actual_column)
            col1, col2 = st.columns(2)

            with col1:
                st.write("基础指标：")
                st.write(f"计划平均值: {analysis_results['计划平均值']:.2f}")
                st.write(f"实际平均值: {analysis_results['实际平均值']:.2f}")
                st.write(f"总体完成率: {analysis_results['总体完成率']:.2f}%")

            with col2:
                st.write("达成情况：")
                st.write(f"超计划次数: {analysis_results['超计划次数']}")
                st.write(f"未达计划次数: {analysis_results['未达计划次数']}")

            # 创建对比图表
            st.subheader("趋势对比图")
            comparison_chart = create_comparison_chart(df_sorted, face_name_column, plan_column, actual_column)
            # 将Pyecharts图表渲染为HTML文件并通过Streamlit显示
            with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as f:
                file_path = f.name
                comparison_chart.render(file_path)
                components.html(open(file_path, 'r').read(), height=600)

            # 创建差异分析图
            st.subheader("差异分析图")
            variance_chart = create_variance_chart(df_sorted, face_name_column, '差异值')
            # 将Pyecharts图表渲染为HTML文件并通过Streamlit显示
            with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as f:
                file_path = f.name
                variance_chart.render(file_path)
                components.html(open(file_path, 'r').read(), height=600)

            # 显示详细的差异数据
            st.subheader("差异详细数据")
            df_display = df_sorted[[face_name_column, plan_column, actual_column, '差异值', '差异百分比']]

            # 重置索引以避免应用样式时的索引问题
            df_display_reset = df_display.reset_index(drop=True)

            # 使用 applymap 来高亮显示差异值和差异百分比
            st.dataframe(df_display_reset.style.applymap(highlight, subset=['差异值', '差异百分比']))


if __name__ == "__main__":
    main()