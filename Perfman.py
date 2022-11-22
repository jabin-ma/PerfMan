import collections
import os
import re

from pyecharts import options as opts
from pyecharts.charts import Pie

from memtype import MEM_TYPE
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
    db = SmapsDatabase("test.db")
    db.padding(dataB.tag, dataB.data)
    db.padding(dataA.tag, dataA.data)


if __name__ == '__main__':
    # renderCompareSummary(
    #     DataSet("settings ", os.popen("adb shell cat /proc/$(pidof com.android.settings)/smaps")),
    #     DataSet('systemui', os.popen("adb shell cat /proc/$(pidof com.android.systemui)/smaps"))
    # )
    test = '/system/framework/boot-framework.art'
    for dict_item in MEM_TYPE:
        rex = dict_item['regex']
        if re.search(rex, test):
            type_str = dict_item['type']
            if 'subtype' in dict_item:
                type_str += '-'
                type_str += dict_item['subtype']

            print('{} {}'.format(rex,type_str))


    # db = SmapsDatabase()
    #
    # db.padding('settings', os.popen("adb shell cat /proc/$(pidof com.android.settings)/smaps"))
    # result = db.execute('select * from smaps where tag=\'settings\' limit 5')
    # result_list = [d for d in result]
    # DataSet('AAA', os.popen("adb shell cat /proc/$(pidof com.android.settings)/smaps"))
    # #
    # db.padding('systemui', os.popen("adb shell cat /proc/$(pidof com.android.systemui)/smaps"))
    # result = db.execute('select * from smaps where tag=\'systemui\'  limit 5')
    # result_list2 = [d for d in result]
