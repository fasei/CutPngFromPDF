# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Aug 13 14:44:34 2019
    当前为改进版本，功能仅为查找横版的pdf文件，将文件拷贝到统一文件夹
@author: 王超
"""

from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFTextExtractionNotAllowed
from PIL import Image
import fitz
import re
import os
import random
from shutil import copyfile


class GetPic:

    def __init__(self, filename, password=''):
        """
        初始化
        :param filename: pdf路径
        :param password: 密码
        """
        with open(filename, 'rb') as file:
            # 创建文档分析器
            self.parser = PDFParser(file)
        # 创建文档
        self.doc = PDFDocument()
        # 连接文档与文档分析器
        self.parser.set_document(self.doc)
        self.doc.set_parser(self.parser)
        # 初始化, 提供初始密码, 若无则为空字符串
        self.doc.initialize(password)
        # 检测文档是否提供txt转换, 不提供就忽略, 抛出异常
        if not self.doc.is_extractable:
            raise PDFTextExtractionNotAllowed
        else:
            # 创建PDF资源管理器, 管理共享资源
            self.resource_manager = PDFResourceManager()
            # 创建一个PDF设备对象
            self.laparams = LAParams()
            self.device = PDFPageAggregator(self.resource_manager, laparams=self.laparams)
            # 创建一个PDF解释器对象
            self.interpreter = PDFPageInterpreter(self.resource_manager, self.device)
            # pdf的page对象列表
            self.doc_pdfs = list(self.doc.get_pages())
        #  打开PDF文件, 生成一个包含图片doc对象的可迭代对象
        self.doc_pics = fitz.open(filename)

    def to_pic(self, doc, zoom, pg, pic_path):
        """
        将单页pdf转换为pic
        :param doc: 图片的doc对象
        :param zoom: 图片缩放比例, type int, 数值越大分辨率越高
        :param pg: 对象在doc_pics中的索引
        :param pic_path: 图片保存路径
        :return: 图片的路径
        """
        rotate = int(0)
        trans = fitz.Matrix(zoom, zoom).preRotate(rotate)
        pm = doc.getPixmap(matrix=trans, alpha=False)
        path = os.path.join(pic_path, str(pg)) + '.png'
        pm.writePNG(path)
        return path

    def get_pic_loc(self, doc, tmp=''):
        """
        获取单页中图片的位置，输出文本
        :param doc: pdf的doc对象
        :return: 返回一个list, 元素为图片名称和上下y坐标元组组成的tuple. 当前页的尺寸
        """
        self.interpreter.process_page(doc)
        layout = self.device.get_result()
        # pdf的尺寸, tuple, (width, height)
        canvas_size = layout.bbox
        # 图片名称坐标
        loc_top = []
        # 来源坐标
        loc_bottom = []
        # 图片名称与应截取的区域y1, y2坐标
        loc_named_pic = []
        # 遍历单页的所有LT对象
        text_export = ''
        # 输出文本信息

        topNumber = 0
        bottomNumber = 0

        for i in layout:
            # print('读取变量数据',i)
            if hasattr(i, 'get_text'):
                text = i.get_text().strip()
                text_export += text
                # 匹配关键词
                if re.search(r'^(图表*|表)(\s|\s*\d|\s*[:：])', text):
                    loc_top.append((i.bbox, text))
                    topNumber = topNumber + 1
                elif re.search(r'^(来源)|(资料来源)(\s|[:：])', text):
                    bottomNumber = bottomNumber + 1
                    loc_bottom.append((i.bbox, text))
        locname = []

        print('读取一页的结果：topNumber.', topNumber, '     bottomNumber.', bottomNumber)

        i0 = 0
        j0 = 0
        #        size_increase = 10 #

        name = ''
        print(loc_top)
        print(loc_bottom)
        print(len(loc_top),len(loc_bottom))
        # 这里逻辑有点乱。将loc_top和loc_bottom依y轴坐标对齐，以找出

        if len(loc_top) == 1 and len(loc_bottom) == 0:
            try:
                name = locname[0][0][1]
            except:
                name = ''
        elif len(loc_top) > 0 and len(loc_bottom) > 0:
            while i0 <= len(loc_top) - 1 and j0 <= len(loc_bottom) - 1:
                #  print (i0,j0)
                if loc_top[i0][0][1] < loc_bottom[j0][0][1]:  # 如果尾的y轴坐标值大于头的坐标值（y轴坐标由下往上递增  范围为0到正无穷）
                    bottom = [(0, loc_bottom[j0][0][1], canvas_size[2], loc_bottom[j0][0][3]), loc_bottom[j0][1]]
                    locname.append([bottom, 1])
                    j0 += 1
                    continue
                is_binglie = 0  # 判定是否一行两个图
                try:
                    if abs(loc_top[i0][0][1] - loc_top[i0 + 1][0][1]) < 10:  # 纵坐标相差不大
                        is_binglie = 1
                except:
                    pass

                if is_binglie == 0:
                    if loc_top[i0][0][1] > loc_bottom[j0][0][1]:  # 非并列时，最正常的上下关系图情况
                        top = [(0, loc_top[i0][0][1], canvas_size[2], loc_top[i0][0][3]),
                               loc_top[i0][1]]  # (x1,y1,x2,y2)
                        locname.append([top, 0])
                        i0 += 1
                    else:
                        bottom = [(0, loc_bottom[j0][0][1], canvas_size[2], loc_bottom[j0][0][3]), loc_bottom[j0][1]]
                        locname.append([bottom, 1])
                        j0 += 1

                else:
                    is_binglie_laiyuan = 0
                    try:
                        if abs(loc_bottom[j0][0][1] - loc_bottom[j0 + 1][0][1]) < 10:
                            is_binglie_laiyuan = 2
                        else:
                            is_binglie_laiyuan = 1
                    except:
                        try:
                            loc_bottom[j0][0][1]
                            is_binglie_laiyuan = 1
                        except:
                            is_binglie_laiyuan = 0

                    if is_binglie_laiyuan == 2:
                        top1 = [(0, loc_top[i0][0][1], loc_top[i0 + 1][0][0], loc_top[i0][0][3]), loc_top[i0][1]]
                        locname.append([top1, 0])

                        bottom1 = [(0, loc_bottom[j0][0][1], loc_top[i0 + 1][0][0], loc_bottom[j0][0][3]),
                                   loc_bottom[j0][1]]
                        locname.append([bottom1, 1])

                        top2 = [(loc_top[i0 + 1][0][0], loc_top[i0 + 1][0][1], canvas_size[2], loc_top[i0 + 1][0][3]),
                                loc_top[i0 + 1][1]]
                        locname.append([top2, 0])

                        bottom2 = [
                            (loc_top[i0 + 1][0][0], loc_bottom[j0 + 1][0][1], canvas_size[2], loc_bottom[j0 + 1][0][3]),
                            loc_bottom[j0 + 1][1]]
                        locname.append([bottom2, 1])
                        i0 += 2
                        j0 += 2
                    elif is_binglie_laiyuan == 1:

                        top1 = [(0, loc_top[i0][0][1], loc_top[i0 + 1][0][0], loc_top[i0][0][3]), loc_top[i0][1]]
                        locname.append([top1, 0])

                        bottom1 = [(0, loc_bottom[j0][0][1], loc_top[i0 + 1][0][0], loc_bottom[j0][0][3]),
                                   loc_bottom[j0][1]]
                        locname.append([bottom1, 1])

                        top2 = [(loc_top[i0 + 1][0][0], loc_top[i0 + 1][0][1], canvas_size[2], loc_top[i0 + 1][0][3]),
                                loc_top[i0 + 1][1]]
                        locname.append([top2, 0])

                        bottom2 = [(loc_top[i0 + 1][0][0], loc_bottom[j0][0][1], canvas_size[2], loc_bottom[j0][0][3]),
                                   loc_bottom[j0][1]]
                        locname.append([bottom2, 1])
                        i0 += 2
                        j0 += 1
                    else:
                        top1 = [(0, loc_top[i0][0][1], loc_top[i0 + 1][0][0], loc_top[i0][0][3]), loc_top[i0][1]]
                        top2 = [(loc_top[i0 + 1][0][0], loc_top[i0 + 1][0][1], canvas_size[2], loc_top[i0 + 1][0][3]),
                                loc_top[i0 + 1][1]]
                        locname.append([top1, 0])
                        locname.append([top2, 0])
                        i0 += 2

            if i0 == len(loc_top):
                while j0 <= len(loc_bottom) - 1:
                    locname.append([loc_bottom[j0], 1])
                    j0 += 1
            if j0 == len(loc_bottom):
                while i0 <= len(loc_top) - 1:
                    locname.append([loc_top[i0], 0])
                    i0 += 1

            if i0 == len(loc_top):
                while j0 <= len(loc_bottom) - 1:
                    locname.append([loc_bottom[j0], 1])
                    j0 += 1
            if j0 == len(loc_bottom):
                while i0 <= len(loc_top) - 1:
                    locname.append([loc_top[i0], 0])
                    i0 += 1
            k = 0
            loc_named_pic = []
            #  print(locname)

            '''
            将locname转为loc_named_pic
            '''
            while k <= len(locname) - 1:
                #   print(k)
                if locname[0][1] == 1:  # 第一行是表尾，定义x1，x2为pdf宽度，y1为pdf顶，y2为表尾坐标
                    x1 = canvas_size[0]
                    x2 = canvas_size[2]
                    y1 = canvas_size[3]
                    y2 = locname[0][0][0][3]
                    name = tmp
                    loc_named_pic.append([name, (x1, y1, x2, y2)])
                    name = ''
                    k += 1

                elif locname[k][1] == 0:  # 找到第一个表头
                    name += locname[k][0][1]
                    if k + 1 < len(locname):  # k 是表头行
                        ii = k + 1
                        while ii < len(locname):  ##ii 找表尾
                            if locname[ii][1] == 0:  ## ii不是表尾
                                name += ' ' + locname[ii][0][1]
                                ii += 1
                            else:  ## ii是表尾
                                x1 = locname[k][0][0][0]
                                x2 = locname[k][0][0][2]
                                y1 = locname[k][0][0][3]
                                y2 = locname[ii][0][0][1]
                                loc_named_pic.append([name, (x1, y1, x2, y2)])
                                name = ''
                                k = ii + 1
                                ii += 1
                                continue
                        k += 1
                    else:
                        k += 1
                else:
                    k += 1

        tmp = name

        return loc_named_pic, canvas_size, tmp, topNumber, bottomNumber

    def get_crops(self, pic_path, canvas_size, position, cropped_pic_name, cropped_pic_path):
        """
        按给定位置截取图片
        :param pic_path: 被截取的图片的路径
        :param canvas_size: 图片为pdf时的尺寸, tuple, (0, 0, width, height)
        :param position: 要截取的位置, tuple, (y1, y2)
        :param cropped_pic_name: 截取的图片名称
        :param cropped_pic_path: 截取的图片保存路径
        :return:
        """
        img = Image.open(pic_path)
        # 当前图片的尺寸 tuple(width, height)
        pic_size = img.size
        # 截图的范围扩大值

        count = 0
        size_increase = 10
        ##没改完
        x1 = max(position[0] - size_increase, 0) * (pic_size[0] / canvas_size[2])
        x2 = min(position[2] + size_increase, canvas_size[2]) * (pic_size[0] / canvas_size[2])
        #  y1 = pic_size[1] * (1 - (position[0] + size_increase)/canvas_size[3])
        #  y2 = pic_size[1] * (1 - (position[1] - size_increase)/canvas_size[3])
        y1 = max(0, (1 - (position[1] + size_increase) / canvas_size[3]) * pic_size[1])
        y2 = min(pic_size[1], (1 - (position[3] - size_increase) / canvas_size[3]) * pic_size[1])

        #  print(x1,x2,y1,y2)
        cropped_img = img.crop((x1, y1, x2, y2))
        cropped_pic_name = cropped_pic_name + str(count)
        cropped_pic_name = cropped_pic_name.replace('/', '')
        cropped_pic_name = cropped_pic_name.replace('  ', '')
        cropped_pic_name = cropped_pic_name.replace('\\', '')
        cropped_pic_name = cropped_pic_name.replace(':', '')
        cropped_pic_name = cropped_pic_name.replace('*', '')
        cropped_pic_name = cropped_pic_name.replace('?', '')
        cropped_pic_name = cropped_pic_name.replace('"', '')
        cropped_pic_name = cropped_pic_name.replace('<', '')
        cropped_pic_name = cropped_pic_name.replace('>', '')
        cropped_pic_name = cropped_pic_name.replace('|', '')
        cropped_pic_name = cropped_pic_name.replace('\n', '')
        cropped_pic_name = cropped_pic_name.replace('\r', '')
        cropped_pic_name = cropped_pic_name.replace('\f', '')
        if len(cropped_pic_name) > 50:
            cropped_pic_name = cropped_pic_name[0:49]
        count += 1
        rand0 = str(random.randint(10000000, 99999999))
        text0 = []
        log0 = []
        try:
            path = os.path.join(cropped_pic_path, rand0) + '.png'
            cropped_img.save(path)
            text0 = cropped_pic_name + '|' + rand0 + '|' + str(x1) + '|' + str(x2) + '|' + str(y1) + '|' + str(y2)
            # print(text0)
            return text0, log0

        # print('成功截取图片:', cropped_pic_name)
        except:
            log0 = cropped_pic_path + cropped_pic_name
            print('失败', cropped_pic_name)
            return text0, log0
            # pass

    def main(self, pic_path, cropped_pic_path, pgn=None, tmp=''):
        """
        主函数
        :param pic_path: 被截取的图片路径
        :param cropped_pic_path: 图片的截图的保存路径
        :param pgn: 指定获取截图的对象的索引
        :return:
        """
        text_total = []
        log_total = []
        topNumber = 0
        bottomNumber = 0
        hasFindHengPng=0
        if pgn is not None:
            # 获取当前页的doc
            doc_pdf = self.doc_pdfs[pgn]
            doc_pic = self.doc_pics[pgn]
            # 将当前页转换为PNG, 返回值为图片路径
            path = self.to_pic(doc_pic, 2, pgn, pic_path)

            if pgn==0:
                img = Image.open(path)  # 打开当前路径图像
                width = img.size[0]
                height = img.size[1]
                if width > height:
                    hasFindHengPng=1

            loc_name_pic, canvas_size, tmp, topNumber, bottomNumber = self.get_pic_loc(doc_pdf, tmp=tmp)

            print(pgn)

            if loc_name_pic:
                for i in loc_name_pic:
                    position = i[1]
                    cropped_pic_name = re.sub('/', '_', i[0])
                    text1, log1 = self.get_crops(path, canvas_size, position, cropped_pic_name, cropped_pic_path)
                    if text1:
                        text1 = text1 + '|' + str(pgn)
                        text_total.append(text1)

                        ##写入文件

                    if log1:
                        log1 = log1 + '|第' + str(pgn) + '页出错'
                        log_total.append(log1)
        return tmp, text_total, log_total, topNumber, bottomNumber,hasFindHengPng


'''
import time

time_start=time.time()

if __name__ == '__main__':
    pdf_path = 'c:\\hibor\\pdftest\\201908061601455165.pdf'
    test = GetPic(pdf_path)
    pic_path = 'c:\\hibor\\1\\3'
    cropped_pic_path = 'c:\\hibor\\2\\2'
    page_count = test.doc_pics.pageCount
    tmp=''
    for i in range(page_count):
        test = GetPic(pdf_path)
        tmp=test.main(pic_path, cropped_pic_path, pgn=i,tmp=tmp)
        test=[]

time_end=time.time()
print('time cost',time_end-time_start,'s')
'''


def run(log_file_path,pic_path0, cropped_pic_path0, text_dir, file_dir):
    import warnings
    import time
    time_start = time.time()
    # warnings.filterwarnings("ignore")
    log_total1 = []
    #   file_dir='e:\\pdfreport\\upfile\\'

    for files in os.walk(file_dir):
        count0 = 0

        for pdf_name in files[2]:
            if pdf_name[-3:] == 'pdf':

                text_total1 = []
                count0 += 1
                print(u'第' + str(count0) + u'篇')
                print(u'文件名称' + str(pdf_name) + u'')

                pdf_path = files[0] + '\\' + pdf_name
                path_tmp = pdf_path
                rand1 = str(random.randint(10000000, 99999999))
                print(u'文件夹名称' + str(rand1) + u'')

                pic_path = pic_path0 + rand1
                isExists = os.path.exists(pic_path)
                if not isExists:
                    os.makedirs(pic_path)
                path_tmp = files[0]
                path_tmp = path_tmp.replace(file_dir, '')
                cropped_pic_path = cropped_pic_path0 + path_tmp + '\\' + rand1
                isExists1 = os.path.exists(cropped_pic_path)
                if not isExists1:
                    os.makedirs(cropped_pic_path)

                # 复制文件方便查看
                copyfile(pdf_path, cropped_pic_path0 + rand1 + '\\' + pdf_name)

                path_file_name = text_dir + path_tmp + '\\' + pdf_name[:-4] + '.txt'
                path_file_p = text_dir + path_tmp + '\\'
                isExists0 = os.path.exists(path_file_name)
                isExists2 = os.path.exists(path_file_p)
                if not isExists2:
                    os.makedirs(path_file_p)
                if isExists0:
                    continue
                else:
                    f = open(path_file_name, 'w')
                    f.close()

                tmp = ''

                try:
                    test = GetPic(pdf_path)
                    page_count = test.doc_pics.pageCount
                    findAllTopNumber = 0
                    findAllBottomNumber = 0
                    for i in range(page_count):
                        try:
                            # test = GetPic(pdf_path)
                            tmp, text_total, log_total, topNumber, bottomNumber,hasFind = test.main(pic_path, cropped_pic_path,
                                                                                            pgn=i, tmp=tmp)

                            if hasFind==1:
                                copyfile(pdf_path,  'd:\\hengpdf\\' + pdf_name)
                                break
                            else:
                                break

                            findAllTopNumber = findAllTopNumber + topNumber
                            findAllBottomNumber = findAllBottomNumber + bottomNumber

                            if text_total:
                                for text1 in text_total:
                                    text_total1.append(text1 + '|' + rand1)
                            if log_total:
                                for log1 in log_total:
                                    log_total1.append(log1)

                            # test = []
                        except:
                            log_total1.append(cropped_pic_path + '第' + str(i) + '页出错')
                            # print(u'第'+str(count0)+u'篇第'+str(i)+'页出错')
                except:
                    log_total1.append(cropped_pic_path + '不是pdf')

                # print(u'不是pdf')
                finally:
                    if text_total1:
                        #  path_file_name = cropped_pic_path+'\\data_list.txt'
                        try:
                            with open(path_file_name, "w") as f:
                                cop = re.compile("[^\u4e00-\u9fa5^a-z^A-Z^0-9^\s^.^:^|]")  ##去掉非中英文字符
                                for i in text_total1:
                                    i = cop.sub('', i)
                                    i = i + '\n'
                                    print(i)
                                    f.write(i)
                        except:
                            path_file_name = cropped_pic_path + '\\data_list.txt'
                            with open(path_file_name, "w") as f:
                                f.write('no data')

                    else:
                        path_file_name = cropped_pic_path + '\\data_list.txt'
                        with open(path_file_name, "w") as f:
                            f.write('no data')

                    errorFileName = log_file_path + '666_log' + '.txt'
                    isExists = os.path.exists(log_file_path)
                    if not isExists:
                        os.makedirs(log_file_path)
                    with open(errorFileName, "a+") as f:
                        f.write('findTop:' + str(findAllTopNumber) + ',Bottom:' + str(
                            findAllBottomNumber) + '------原文件名:' + pdf_name + '，截图文件夹名称:' + str(rand1) + '\n')

        log_file_name = log_file_path + str(int(time_start)) + '.txt'
        isExists = os.path.exists(log_file_path)
        if not isExists:
            os.makedirs(log_file_path)
        with open(log_file_name, "w") as f:
            for i in log_total1:
                f.write(i + '\n')


if __name__ == '__main__':
    import time
    import warnings

    # warnings.filterwarnings("ignore")
    log_total1 = []
    # file_dir='d:\\pdfreport\\upfile\\'
    #0201\0202\0203
    file_dir='D:\\upfile201801_07\\2018_2\\2018_02_05\\'
    # file_dir = 'd:\\upfile201801-07\\2018_7\\2018_07_31\\'
    # start='d:\\pdfreport\\t\\'
    start = 'd:\\pdfreport\\mm\\'


    pic_path0 = start+'pic_path\\'
    cropped_pic_path0 =start+ 'cropped_pic_path\\'
    text_dir = start+'text\\'
    #   file_dir= 'e:\\2\\'
    log_file_path = start+'log\\'

    run(log_file_path,pic_path0, cropped_pic_path0, text_dir, file_dir)
'''
##外部传参
file_dir pdf目录
pic_path pic目录
cropped_pic_path 截图目录
log_file_path 日志目录
'''
