import collections
import os

from pyecharts import options as opts
from pyecharts.charts import Pie

from sysmaps import SmapsDatabase


def totalDict(dicts, totalKeys):
    total = 0
    for totalKey in totalKeys:
        total += int(dicts[totalKey])
    return total


def createPie(datas, title) -> Pie:
    pie = Pie()
    pie.add("", datas)
    pie.set_global_opts(title_opts=opts.TitleOpts(title=title),
                        legend_opts=opts.LegendOpts(
                            pos_right="right",
                            orient="vertical",
                            is_show=False)
                        )
    pie.set_series_opts(label_opts=opts.LabelOpts(formatter="{b}  {c} : ({d})%"))
    return pie


def createPieData(pie_data, name_key, value_key):
    pie_data_title = [dict_item[name_key] for dict_item in pie_data]
    pie_data_value = [dict_item[value_key] for dict_item in pie_data]
    print(pie_data_value)
    pie_data = list(zip(pie_data_title, pie_data_value))
    return pie_data


class DataSet:
    tag: str
    data: collections

    def __init__(self, tag, data: collections):
        self.tag = tag
        self.data = data


def renderCompareSummary(dataA: DataSet, dataB: DataSet):
    db = SmapsDatabase()
    db.padding(dataB.tag, dataB.data)
    db.padding(dataA.tag, dataA.data)
    result = db.popColumn(dataA.tag, 'Pss')
    print(result)


if __name__ == '__main__':
    renderCompareSummary(
        DataSet("settings", os.popen('adb shell "cat /proc/$(pidof com.android.settings)/smaps"')),
        DataSet('systemui', os.popen('adb shell "cat /proc/$(pidof com.android.systemui)/smaps"'))
    )
