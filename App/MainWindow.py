
import os

import matplotlib
import matplotlib.pyplot as plt
from PyQt5.QtCore import QTimer, Qt, QStringListModel, QModelIndex
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap
from PyQt5.QtWidgets import QMainWindow, QHeaderView, QMessageBox, QGraphicsPixmapItem, QGraphicsScene

from App.DataCrawler import NBAChina
from App.UI.mainwindow import Ui_MainWindow
import json
import numpy as np


class MainWindow(QMainWindow, Ui_MainWindow):
    file_player_list = os.path.abspath('./App/res/players.json')
    file_players_height = os.path.abspath('./App/res/players_height.json')
    file_players_position = os.path.abspath('./App/res/players_position.json')
    file_players_countries = os.path.abspath('./App/res/players_countries.json')
    path_statics = os.path.abspath('./App/statics')
    path_data = os.path.abspath('./App/data')
    __NBAChina = None
    dict_players = None
    players_list = []
    model = None
    heights = None
    positions = None
    countries = None

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.charts_list = ['', '位置分布柱状图', '位置分布饼图', '国籍分布柱状图', '身高分布饼图']
        self.comboBox.addItems(self.charts_list)
        self.comboBox.currentIndexChanged.connect(self.show_charts)  # 显示图标
        self.pushButton_5.pressed.connect(self.update_data_source)  # 更新数据源文件
        self.pushButton.pressed.connect(self.query_players)  # 查询球员信息
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tableView.horizontalHeader().sectionClicked.connect(self.tableView_head_click)
        self.tableView.doubleClicked.connect(self.tableView_row_dclick)
        self._data_init()
        self.matplotlib_config()

    def _data_init(self):
        font = {'family': 'MicroSoft YaHei',
                'weight': 'normal',
                'size': 5}
        matplotlib.rc("font", **font)
        if not os.path.exists(self.file_player_list) or not os.path.exists(self.file_players_height) \
                or not os.path.exists(self.file_players_position) or not os.path.exists(self.file_players_countries):
            self.start_data_crawler_thread()
        self.dict_players = self.get_dict_from_json_file(self.file_player_list)
        self.positions = self.get_dict_from_json_file(self.file_players_position)
        self.heights = self.get_dict_from_json_file(self.file_players_height)
        self.countries = self.get_dict_from_json_file(self.file_players_countries)
        self.players_list = self.dict_players.values()
        self.show_players_info(self.players_list)

    @staticmethod
    def matplotlib_config():
        font = {'family': 'MicroSoft YaHei',
                'weight': 'normal',
                'size': 10}
        matplotlib.rc("font", **font)
        # params = {
        #     'figure.figsize': '8, 4'
        # }
        # plt.rcParams.update(params)

    def update_data_source(self):
        reply = QMessageBox.question(self, '提示', '更新数据将花费较长时间！是否继续？', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.start_data_crawler_thread()

    # 启动爬虫进程
    def start_data_crawler_thread(self):
        self.pushButton_5.setEnabled(False)
        self.__NBAChina = NBAChina()
        self.__NBAChina.signal.connect(self.show_crawl_process)
        self.__NBAChina.start()
        self.statusbar.showMessage("正在爬取数据请稍等")

    def query_players(self):
        tmp_list = []
        query_en_name = self.lineEdit_5.text().strip()
        query_name = self.lineEdit.text().strip()
        query_team = self.lineEdit_2.text().strip()
        query_position = self.lineEdit_3.text().strip()
        query_country = self.lineEdit_4.text().strip()
        for player in self.players_list:
            if player[0].count(query_en_name):  # 球员英文名查询
                if player[1].count(query_name):  # 球员中文名查询
                    if player[2].count(query_team):  # 球员球队查询
                        if player[3].count(query_position):  # 球员位置查询
                            if player[7].count(query_country):  # 球员国家查询
                                tmp_list.append(player)
        self.show_players_info(tmp_list)

    # 获取NBA所有球员的信息并展示
    def show_players_info(self, players_list):
        try:
            list_header = ['顺序', '英文名', '中文名', '球队', '位置', '身高(米)', '体重(公斤)', '经验(年)', '国籍',
                           '上场次数', '均上场时间', '场均得分', '场均助攻', '场均篮板', '场均抢断', '场均盖帽', '场均失误',
                           '投篮命中率%', '罚球命中率%', '三分命中率%']
            self.model = QStandardItemModel(len(players_list), list_header.__len__())
            self.model.setHorizontalHeaderLabels(list_header)
            i = 0
            for player in players_list:
                item = QStandardItem()
                item.setData(i + 1, Qt.DisplayRole)
                self.model.setItem(i, 0, item)
                for j in range(len(player)):
                    item = QStandardItem()
                    item.setData(player[j], Qt.DisplayRole)
                    self.model.setItem(i, j+1, item)
                i += 1
            self.tableView.setModel(self.model)
        except Exception as e:
            print(e)

    def tableView_head_click(self, index):
        self.model.sort(index, self.tableView.horizontalHeader().sortIndicatorOrder())

    def tableView_row_dclick(self, index):
        row_content_list = []
        current_row_id = index.row()
        column_count = self.model.columnCount()
        for column_id in range(1, column_count):
            row_content_list.append(self.model.item(current_row_id, column_id).text())
        print(row_content_list)
        self.comboBox.setCurrentText('')
        self.radar(row_content_list)

    @staticmethod
    def get_dict_from_json_file(file_name):
        with open(file_name, 'r', encoding='UTF-8') as fp:
            return json.load(fp)

    def show_crawl_process(self, *flag):
        if flag[0] == 'Success':
            self.statusbar.showMessage(flag[1], 5000)
            self._data_init()
            self.pushButton_5.setEnabled(True)
        elif flag[0] == 'Failure':
            self.statusbar.showMessage(flag[1], 5000)
            self.pushButton_5.setEnabled(True)
        elif flag[0] == 'Running':
            self.statusbar.showMessage(flag[1], 5000)

    def show_charts(self):
        current_text = self.comboBox.currentText()
        if current_text == '':
            return
        file_name = os.path.join(self.path_statics, "{}.png".format(current_text))
        if not os.path.exists(file_name):
            plt.rcParams['font.sans-serif'] = ['SimHei']
            if current_text == '位置分布柱状图':
                x = [i for i in self.positions]
                y = [self.positions[i] for i in self.positions]
                plt.bar(x, height=y, width=0.8, tick_label=x)
                for a, b, label in zip(x, y, y):
                    plt.text(a, b, label, ha='center', va='bottom')
                # plt.xticks(np.arange(len(x)), x, rotation=30)  # rotation控制倾斜角度
            elif current_text == '位置分布饼图':
                labels = [i for i in self.positions]
                sizes = [self.positions[i] for i in self.positions]
                # 设置分离的距离，0表示不分离
                explode = (0, 0, 0, 0, 0, 0, 0)
                plt.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True, startangle=90)
                # Equal aspect ratio 保证画出的图是正圆形
                plt.axis('equal')
            elif current_text == '国籍分布柱状图':
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
            elif current_text == '身高分布饼图':
                labels = [i for i in self.heights]
                sizes = [self.heights[i] for i in self.heights]
                # 设置分离的距离，0表示不分离
                explode = (0, 0, 0, 0, 0, 0)
                plt.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', shadow=False, startangle=150,
                        pctdistance=0.7)
            plt.savefig(file_name, dpi=150)  #
            plt.clf()
        item = QGraphicsPixmapItem(QPixmap(file_name))
        scene = QGraphicsScene()
        scene.addItem(item)
        self.graphicsView.setScene(scene)

    # 制作雷达图
    def radar(self, player_list):
        try:
            en_name = player_list[0]
            name = player_list[1]
            file_name = os.path.join(self.path_statics, "{}个人数据统计.png".format(name))

            if not os.path.exists(file_name):
                file_player_detail_json = os.path.join(self.path_data, '{}.json'.format(en_name))
                player_detail_dict = self.get_dict_from_json_file(file_player_detail_json)
                player_statics = {"得分": float(player_list[10]),
                                  "助攻": float(player_list[11]),
                                  "篮板": float(player_list[12]),
                                  "抢断": float(player_list[13]),
                                  "盖帽": float(player_list[14])
                                  # '投篮命中率': float(player_list[13]),
                                  # '三分命中率': float(player_list[15])
                                  }  # 创建第一个人的数据
                payload = player_detail_dict.get('payload')
                # 图片生成代码
                fig = plt.figure(figsize=(10, 15))  # figsize=(10, 5)  建立画布
                ax1 = fig.add_subplot(3, 1, 1, polar=True)  # 设置第一个坐标轴为极坐标体系
                fig.subplots_adjust(wspace=0)  # 设置子图间的间距，为子图宽度的40%
                label = np.array([j for j in player_statics.keys()])  # 提取标签
                data1 = np.array([i for i in player_statics.values()]).astype(int)  # 提取第一个人的信息
                angle = np.linspace(0, 2 * np.pi, len(data1), endpoint=False)  # data里有几个数据，就把整圆360°分成几份
                angles = np.concatenate((angle, [angle[0]]))  # 增加第一个angle到所有angle里，以实现闭合
                data1 = np.concatenate((data1, [data1[0]]))  # 增加第一个人的第一个data到第一个人所有的data里，以实现闭合
                # 设置第一个坐标轴
                ax1.set_thetagrids(angles * 180 / np.pi, label, fontproperties="Microsoft Yahei")  # 设置网格标签
                ax1.plot(angles, data1, "o-")
                ax1.set_theta_zero_location('NW')  # 设置极坐标0°位置
                ax1.set_rlim(0, 30)  # 设置显示的极径范围
                ax1.fill(angles, data1, facecolor='g', alpha=0.2)  # 填充颜色
                ax1.set_title("{}雷达图".format(name), fontproperties="SimHei", fontsize=14)  # 设置子标题
                # 绘制球员生涯数据折线图
                dict_statics = {}
                if payload:
                    playerTeams = payload.get('player').get('stats').get('regularSeasonStat').get('playerTeams')
                    for player in playerTeams:
                        if player.get('profile'):
                            year = player.get('season')
                            statAverage = player.get('statAverage')
                            assistsPg = statAverage.get('assistsPg')
                            pointsPg = statAverage.get('pointsPg')
                            stealsPg = statAverage.get('stealsPg')
                            if dict_statics.get(year):
                                dict_statics[year] = [dict_statics.get(year)[0] + assistsPg,
                                                      dict_statics.get(year)[1] + pointsPg,
                                                      dict_statics.get(year)[2] + stealsPg]
                            else:
                                dict_statics[year] = [assistsPg, pointsPg, stealsPg]
                print(dict_statics.keys())
                print(dict_statics.values())
                value_year = [x for x in dict_statics.keys()]
                value_assists = [y[0] for y in dict_statics.values()]
                value_points = [y[1] for y in dict_statics.values()]
                value_steals = [y[2] for y in dict_statics.values()]
                ax2 = fig.add_subplot('312')
                ax2.set_title("{}常规赛生涯数据折线图".format(name), fontproperties="SimHei", fontsize=14)  # 设置子标题
                ax2.plot(value_year, value_assists, 'b-.', label='助攻')
                ax2.plot(value_year, value_points, 'r-', label='得分')
                ax2.plot(value_year, value_steals, 'g:', label='抢断')
                ax2.grid(b=True, which='major', axis='both', alpha=0.5, color='skyblue', linestyle='--', linewidth=1)
                ax2.set_xlabel('赛季')
                ax2.set_ylabel('数据')
                ax2.legend(loc='upper right', fontsize=10, borderaxespad=0.3)
                # 联盟数据对比图
                if payload:
                    leagueSeasonAverage = payload.get('leagueSeasonAverage')
                    pointsPg = leagueSeasonAverage.get('pointsPg')
                    assistsPg = leagueSeasonAverage.get('assistsPg')
                    rebsPg = leagueSeasonAverage.get('rebsPg')
                    stealsPg = leagueSeasonAverage.get('stealsPg')
                    blocksPg = leagueSeasonAverage.get('blocksPg')
                ax3 = fig.add_subplot('313')
                ax3.set_title("{}联盟数据对比图".format(name), fontproperties="SimHei", fontsize=14)  # 设置子标题
                x_index = np.arange(5)  # 柱的索引
                x_data = player_statics.keys()
                y1_data = player_statics.values()
                y2_data = (pointsPg, assistsPg, rebsPg, stealsPg, blocksPg)
                bar_width = 0.35  # 定义一个数字代表每个独立柱的宽度
                ax3.bar(x_index, y1_data, width=bar_width, alpha=0.4, color='b', label='个人数据')  # 参数：左偏移、高度、柱宽、透明度、颜色、图例
                ax3.bar(x_index + bar_width, y2_data, width=bar_width, alpha=0.5, color='r', label='联盟平均数据')  # 参数：左偏移、高度、柱宽、透明度、颜色、图例
                # 关于左偏移，不用关心每根柱的中心不中心，因为只要把刻度线设置在柱的中间就可以了
                plt.xticks(x_index + bar_width / 2, x_data)  # x轴刻度线
                plt.legend()  # 显示图例
                # 图表配置
                plt.tight_layout()  # 自动调整、填充、消除子图之间的重叠
                plt.savefig(file_name)
                plt.clf()
            item = QGraphicsPixmapItem(QPixmap(file_name))
            scene = QGraphicsScene()
            scene.addItem(item)
            self.graphicsView.setScene(scene)
            self.tabWidget_2.setCurrentIndex(1)
        except Exception as e:
            print(e)




