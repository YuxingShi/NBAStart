# coding:utf-8
import os
from PyQt5.QtCore import pyqtSignal, QThread
import requests
import urllib3
import json
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

urllib3.disable_warnings()


class NBAChina(QThread):

    signal = pyqtSignal(str, str)
    user_agent = 'User-Agent: Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Maxthon 2.0)'
    headers = {'User-Agent': user_agent}
    data_path = os.path.abspath('./App/data')
    res_path = os.path.abspath('./App/res')
    path_statics = os.path.abspath('./App/statics')
    file_player_list = os.path.abspath('./App/data/playerlist.json')
    url_player_list = 'http://china.nba.com/static/data/league/playerlist.json'
    url_player_statistics = 'https://china.nba.com/static/data/player/{}_{}.json'
    players_dict = {}
    dict_player_detail = {}
    positions = {"后卫": 0, "前锋": 0, "中锋": 0, "中锋-前锋": 0, "前锋-中锋": 0, "前锋-后卫": 0, "后卫-前锋": 0}
    heights = {"小于1.80M": 0, "1.80M-1.90M": 0, "1.90M-2.00M": 0, "2.00M-2.10M": 0, "2.10M-2.20M": 0, "大于2.20": 0}  # >1.80;1.80-1.90,1.90-2.00,2.00-2.10,2.10-2.20,<2.20
    countries = {}
    charts_list = ['位置分布柱状图', '位置分布饼图', '国籍分布柱状图', '身高分布饼图']

    def __init__(self):
        super(NBAChina, self).__init__()

    def run(self):
        try:
            r = requests.get(self.url_player_list, headers=self.headers, verify=False)
            if r.status_code == 200:
                dict_players_list = json.loads(r.text)
                self.save_dict_to_file(dict_players_list, self.file_player_list)  # 将原始数据存储到json文件中
                players_list = dict_players_list.get('payload').get('players')
                for player in players_list:
                    playerProfile = player.get('playerProfile')
                    teamProfile = player.get('teamProfile')
                    player_code = playerProfile.get('code').replace(' ', '_')  # 解决姓名中含有空格
                    displayName = playerProfile.get('displayName')
                    name = teamProfile.get('name')
                    position = playerProfile.get('position')
                    height = float(playerProfile.get('height'))
                    weight = float(playerProfile.get('weight').split(' ')[0])
                    experience = int(playerProfile.get('experience'))
                    country = playerProfile.get('country')
                    pointsPg = 0
                    assistsPg = 0
                    rebsPg = 0
                    stealsPg = 0
                    blocksPg = 0
                    foulsPg = 0
                    fgpct = 0
                    ftpct = 0
                    tppct = 0
                    if player_code:
                        print('正在爬取【%s】' % player_code)
                        url_tmp = self.url_player_statistics.format('stats', player_code)
                        r = requests.get(url_tmp, headers=self.headers, verify=False)
                        if r.status_code == 200:
                            self.dict_player_detail.clear()
                            self.dict_player_detail = json.loads(r.text)
                            file_player_detail = os.path.join(self.data_path, '%s.json' % player_code)
                            self.save_dict_to_file(self.dict_player_detail, file_player_detail)
                            payload = self.dict_player_detail.get('payload')

                            if payload:
                                stats = payload.get('player').get('stats')
                                # 常规赛生涯数据平均值统计
                                statAverage = stats.get('regularSeasonCareerStat').get('statAverage')
                                games = float(statAverage.get('games') or 0)
                                minsPg = float(statAverage.get('minsPg') or 0)
                                pointsPg = float(statAverage.get('pointsPg') or 0)
                                assistsPg = float(statAverage.get('assistsPg') or 0)
                                rebsPg = float(statAverage.get('rebsPg') or 0)
                                stealsPg = float(statAverage.get('stealsPg') or 0)
                                blocksPg = float(statAverage.get('blocksPg') or 0)
                                foulsPg = float(statAverage.get('foulsPg') or 0)
                                fgpct = float(statAverage.get('fgpct') or 0)  # 投篮命中率
                                ftpct = float(statAverage.get('ftpct') or 0)  # 罚球命中率
                                tppct = float(statAverage.get('tppct') or 0)  # 三分命中率
                        self.height_statics(height)
                        self.countries_statics(country)
                        self.position_statics(position)
                        self.players_dict[player_code] = [player_code, displayName, name, position, height, weight, experience,
                                                          country, games, minsPg, pointsPg, assistsPg, rebsPg, stealsPg,
                                                          blocksPg, foulsPg, fgpct, ftpct, tppct]
                        self.signal.emit('Running', '【%s】爬取成功！' % player_code)
                file_players_dict = os.path.join(self.res_path, 'players.json')
                self.save_dict_to_file(self.players_dict, file_players_dict)
                # 统计数据生成json文件
                file_players_height_dict = os.path.join(self.res_path, 'players_height.json')
                self.save_dict_to_file(self.heights, file_players_height_dict)
                file_players_position_dict = os.path.join(self.res_path, 'players_position.json')
                self.save_dict_to_file(self.positions, file_players_position_dict)
                file_players_countries_dict = os.path.join(self.res_path, 'players_countries.json')
                self.save_dict_to_file(self.countries, file_players_countries_dict)
                self.clear_statics_graphics()  # 删除统计报表数据
                self.generate_charts()  # 生成统计图
                self.signal.emit('Success', '数据爬取完成！')
            else:
                self.signal.emit('Failure', '未爬取到球员列表，请检查网络！')
        except Exception as e:
            self.clear_statics_graphics()  # 删除统计报表数据
            self.generate_charts()
            self.signal.emit('Success', '数据爬取完成！')

    @staticmethod
    def save_dict_to_file(obj, file_name):
        with open(file_name, 'w', encoding='utf-8') as fp:
            json.dump(obj, fp)

    def height_statics(self, height):
        if height < 1.80:
            self.heights["小于1.80M"] += 1
        elif 1.80 <= height < 1.90:
            self.heights["1.80M-1.90M"] += 1
        elif 1.90 <= height < 2.00:
            self.heights["1.90M-2.00M"] += 1
        elif 2.00 <= height < 2.10:
            self.heights["2.00M-2.10M"] += 1
        elif 2.10 <= height < 2.20:
            self.heights["2.10M-2.20M"] += 1
        else:
            self.heights["大于2.20"] += 1

    def countries_statics(self, country):
        if not self.countries.get(country):
            self.countries[country] = 1
        else:
            self.countries[country] += 1

    def position_statics(self, position):
        s = self.positions.get(position)
        self.positions[position] = s + 1

    def clear_statics_graphics(self):
        file_list = os.listdir(self.path_statics)
        for file in file_list:
            os.remove(os.path.join(self.path_statics, file))

    def generate_charts(self):
        for chart_name in self.charts_list:
            file_save_graphic = os.path.join(self.path_statics, '{}.png'.format(chart_name))
            plt.rcParams['font.sans-serif'] = ['SimHei']
            if chart_name == '位置分布柱状图':
                x = [i for i in self.positions]
                y = [self.positions[i] for i in self.positions]
                plt.bar(x, height=y, width=0.8, tick_label=x)
                for a, b, label in zip(x, y, y):
                    plt.text(a, b, label, ha='center', va='bottom')
                # plt.xticks(np.arange(len(x)), x, rotation=30)  # rotation控制倾斜角度
            elif chart_name == '位置分布饼图':
                labels = [i for i in self.positions]
                sizes = [self.positions[i] for i in self.positions]
                # 设置分离的距离，0表示不分离
                explode = (0, 0, 0, 0, 0, 0, 0)
                plt.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True, startangle=90)
                # Equal aspect ratio 保证画出的图是正圆形
                plt.axis('equal')
            elif chart_name == '国籍分布柱状图':
                font = {'family': 'MicroSoft YaHei',
                        'weight': 'normal',
                        'size': 6}
                matplotlib.rc("font", **font)
                # 对国家球员数字典进行排序
                fig, ax = plt.subplots()
                sorted_items = sorted(self.countries.items(), key=lambda kv: (kv[1], kv[0]))  # , reverse=True
                x = [i[0] for i in sorted_items]
                y = [i[1] for i in sorted_items]
                y_pos = np.arange(len(x))
                ax.set_yticklabels(x)
                # 图像绘制
                b = ax.barh(range(len(x)), y)
                ax.set_yticks(y_pos)
                # 添加数据标签
                for rect in b:
                    w = rect.get_width()
                    ax.text(w, rect.get_y() + rect.get_height() / 2, '%d' % int(w), ha='left', va='center')
                # plt.show()
            elif chart_name == '身高分布饼图':
                labels = [i for i in self.heights]
                sizes = [self.heights[i] for i in self.heights]
                # 设置分离的距离，0表示不分离
                explode = (0, 0, 0, 0, 0, 0)
                plt.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', shadow=False, startangle=150,
                        pctdistance=0.7)
            plt.savefig(file_save_graphic, dpi=150)  #
            plt.clf()






