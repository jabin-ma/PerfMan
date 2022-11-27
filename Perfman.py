import collections
import os

from pyecharts import options as opts
from pyecharts.charts import Pie, Grid

from sysmaps import SmapsDatabase


def totalDict(dicts, totalKeys):
    total = 0
    for totalKey in totalKeys:
        total += int(dicts[totalKey])
    return total


def createPie(datas, title, center=None, radius='100%', title_pos_left='5%') -> Pie:
    if center is None:
        center = ['50%', '50%']
    pie = Pie()
    pie.add(title, datas, center=center, radius=radius)
    pie.set_global_opts(title_opts=opts.TitleOpts(title=title, pos_left=title_pos_left),
                        legend_opts=opts.LegendOpts(
                            pos_left=title_pos_left,
                            is_show=True)
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
    result = db.popColumn(dataA.tag, 'Pss', order=True, limit=5)
    pie_data = createPieData(result, 'name', 'Pss')
    pie = createPie(pie_data, title=dataA.tag +'-PSS', center=['30%', '30%'], radius='30%')

    result = db.popColumn(dataB.tag, 'Pss', order=True, limit=5)
    pie_data = createPieData(result, 'name', 'Pss')
    pie2 = createPie(pie_data, title=dataB.tag +'-PSS', center=['70%', '30%'], radius='30%', title_pos_left='50%')


    grid = Grid(init_opts=opts.InitOpts(width='100%', height='1080px'))
    grid.add(pie, grid_opts=opts.GridOpts())
    grid.add(pie2, grid_opts=opts.GridOpts())
    grid.render('a.html')


if __name__ == '__main__':
    renderCompareSummary(
        DataSet("settings", os.popen('adb shell "cat /proc/$(pidof com.android.settings)/smaps"')),
        DataSet('systemui', os.popen('adb shell "cat /proc/$(pidof com.android.systemui)/smaps"'))
    )
