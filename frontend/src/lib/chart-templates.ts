import type { ChartType } from '@/types/card';

export interface ChartTemplate {
  type: ChartType;
  name: string;
  description: string;
  code: string;
}

export const chartTemplates: Record<ChartType, ChartTemplate> = {
  'summary-number': {
    type: 'summary-number',
    name: 'Summary Number',
    description: '大きな数字 + トレンド表示',
    code: `def render(dataset, filters, params):
    import pandas as pd

    # -- 設定 --
    value_column = dataset.columns[0]  # 集計対象カラムを指定
    agg_func = "sum"                   # sum / mean / count / max / min

    # -- 集計 --
    current_value = dataset[value_column].agg(agg_func)

    # -- フォーマット --
    if current_value >= 1_000_000:
        display = f"{current_value / 1_000_000:.1f}M"
    elif current_value >= 1_000:
        display = f"{current_value / 1_000:.1f}K"
    else:
        display = f"{current_value:,.0f}"

    html = f"""
    <div style="display:flex;flex-direction:column;align-items:center;
                justify-content:center;height:100%;font-family:sans-serif;">
        <div style="font-size:48px;font-weight:700;color:#1a1a2e;">{display}</div>
        <div style="font-size:14px;color:#6b7280;margin-top:8px;">{value_column}</div>
    </div>
    """
    return HTMLResult(html=html)
`,
  },
  bar: {
    type: 'bar',
    name: 'Bar Chart',
    description: '棒グラフ',
    code: `def render(dataset, filters, params):
    import plotly.express as px

    # -- 設定 --
    x_column = dataset.columns[0]  # X軸カラムを指定
    y_column = dataset.columns[1]  # Y軸カラムを指定

    # -- チャート生成 --
    fig = px.bar(
        dataset,
        x=x_column,
        y=y_column,
        title=f"{y_column} by {x_column}",
    )
    fig.update_layout(
        height=400,
        showlegend=False,
    )

    return HTMLResult(html=fig.to_html())
`,
  },
  line: {
    type: 'line',
    name: 'Line Chart',
    description: '折れ線グラフ',
    code: `def render(dataset, filters, params):
    import plotly.express as px

    # -- 設定 --
    x_column = dataset.columns[0]  # X軸カラムを指定
    y_column = dataset.columns[1]  # Y軸カラムを指定

    # -- チャート生成 --
    fig = px.line(
        dataset,
        x=x_column,
        y=y_column,
        title=f"{y_column} over {x_column}",
    )
    fig.update_layout(
        height=400,
        showlegend=False,
    )

    return HTMLResult(html=fig.to_html())
`,
  },
  pie: {
    type: 'pie',
    name: 'Pie Chart',
    description: '円グラフ',
    code: `def render(dataset, filters, params):
    import plotly.express as px

    # -- 設定 --
    names_column = dataset.columns[0]  # カテゴリカラムを指定
    values_column = dataset.columns[1]  # 値カラムを指定

    # -- チャート生成 --
    fig = px.pie(
        dataset,
        names=names_column,
        values=values_column,
        title=f"{values_column} by {names_column}",
    )
    fig.update_layout(
        height=400,
    )

    return HTMLResult(html=fig.to_html())
`,
  },
  table: {
    type: 'table',
    name: 'Table',
    description: 'テーブル',
    code: `def render(dataset, filters, params):
    import pandas as pd

    # -- テーブル生成 --
    html_table = dataset.to_html(
        classes="table-auto w-full",
        table_id="data-table",
        escape=False,
    )

    html = f"""
    <div style="overflow-x:auto;width:100%;height:100%;">
        <style>
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; font-weight: bold; }}
        </style>
        {html_table}
    </div>
    """
    return HTMLResult(html=html)
`,
  },
  pivot: {
    type: 'pivot',
    name: 'Pivot Table',
    description: 'ピボットテーブル',
    code: `def render(dataset, filters, params):
    import pandas as pd

    # -- 設定 --
    index_column = dataset.columns[0]  # 行カラムを指定
    columns_column = dataset.columns[1] if len(dataset.columns) > 1 else None  # 列カラムを指定（オプション）
    values_column = dataset.columns[-1]  # 値カラムを指定
    agg_func = "sum"  # sum / mean / count / max / min

    # -- ピボットテーブル生成 --
    if columns_column:
        pivot_table = pd.pivot_table(
            dataset,
            index=index_column,
            columns=columns_column,
            values=values_column,
            aggfunc=agg_func,
            fill_value=0,
        )
    else:
        pivot_table = pd.pivot_table(
            dataset,
            index=index_column,
            values=values_column,
            aggfunc=agg_func,
        )

    html_table = pivot_table.to_html(
        classes="table-auto w-full",
        table_id="pivot-table",
        escape=False,
    )

    html = f"""
    <div style="overflow-x:auto;width:100%;height:100%;">
        <style>
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; font-weight: bold; }}
        </style>
        {html_table}
    </div>
    """
    return HTMLResult(html=html)
`,
  },
};

export function getChartTemplate(chartType: ChartType): ChartTemplate {
  return chartTemplates[chartType];
}

export function getAllChartTypes(): ChartType[] {
  return Object.keys(chartTemplates) as ChartType[];
}
