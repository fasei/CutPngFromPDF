# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

# -*- coding: utf-8 -*-
from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFTextExtractionNotAllowed
from PIL import Image
import fitz
import re
import os
from shutil import copyfile
from configparser import ConfigParser
import time

class GetPic:

    def __init__(self, filename, password=''):
        try:
            
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
        except Exception as e:
            log_file_name=text_dir + 'log' + '.txt'
            isExists = os.path.exists(text_dir)
            if not isExists:
                os.makedirs(text_dir)
            with open(log_file_name, "a+",encoding='utf-8') as f:
                f.write('\n__init__|'+file_dir+'|'+filename+'|' + str(e))

    def to_pic(self, doc, zoom, pg, pic_path):
        """
        将单页pdf转换为pic
        :param doc: 图片的doc对象
        :param zoom: 图片缩放比例, type int, 数值越大分辨率越高
        :param pg: 对象在doc_pics中的索引
        :param pic_path: 图片保存路径
        :return: 图片的路径
        """
        try:
            rotate = int(0)
            trans = fitz.Matrix(zoom, zoom).preRotate(rotate)
            pm = doc.getPixmap(matrix=trans, alpha=True)
            path = os.path.join(pic_path, str(pg)) + '.png'
            pm.writePNG(path)
            return path
        except Exception as e:
            log_file_name=text_dir + 'log' + '.txt'
            isExists = os.path.exists(text_dir)
            if not isExists:
                os.makedirs(text_dir)
            with open(log_file_name, "a+",encoding='utf-8') as f:
                f.write('\nto_pic|'+file_dir+'|' + str(e))

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
            if hasattr(i, 'get_text'):
                text = i.get_text().strip()
                text_export += text
                # 匹配关键词
                if re.search(r'^(图表*|表)(\s|\s*\d|\s*[:：])', text):
                    loc_top.append((i.bbox, text))
                    topNumber = topNumber + 1
                elif re.search(r'^((来源)|(资料来源)|(数据来源))(\s|[:：])', text):
                    bottomNumber = bottomNumber + 1
                    loc_bottom.append((i.bbox, text))
                elif re.search(r'\n+((来源)|(资料来源)|(数据来源))(\s|[:：])', text):
                    bottomNumber = bottomNumber + 1
                    loc_bottom.append((i.bbox, text))

        locname = []
        
        i0 = 0
        j0 = 0

        name = ''
        # 这里逻辑有点乱。将loc_top和loc_bottom依y轴坐标对齐，以找出

        if len(loc_top) == 1 and len(loc_bottom) == 0:
            try:
                name = locname[0][0][1]
            except:
                name = ''
        elif len(loc_top) > 0 and len(loc_bottom) > 0:
            while i0 <= len(loc_top) - 1 and j0 <= len(loc_bottom) - 1:
                if loc_top[i0][0][1] < loc_bottom[j0][0][1]:  # 如果尾的y轴坐标值大于头的坐标值（y轴坐标由下往上递增 范围为0到正无穷）
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

                if is_binglie == 0:  # 只有一行的时候
                    if loc_top[i0][0][1] > loc_bottom[j0][0][1]:  # 非并列时，最正常的上下关系图情况
                        top = [(0, loc_top[i0][0][1], canvas_size[2], loc_top[i0][0][3]),
                               loc_top[i0][1]]  # (x1,y1,x2,y2)
                        locname.append([top, 0])
                        i0 += 1
                    else:  # 获取队列中尾部编辑后的坐标
                        bottom = [(0, loc_bottom[j0][0][1], canvas_size[2], loc_bottom[j0][0][3]), loc_bottom[j0][1]]
                        locname.append([bottom, 1])
                        j0 += 1

                else:  ## 有并列头部数据的时候
                    is_binglie_laiyuan = 0
                    try:
                        if abs(loc_bottom[j0][0][1] - loc_bottom[j0 + 1][0][1]) < 10:
                            is_binglie_laiyuan = 2
                        else:
                            is_binglie_laiyuan = 1
                    except:
                        try:
                            loc_bottom[j0][0][1]  # 如果没有尾的来源
                            is_binglie_laiyuan = 1
                        except:
                            is_binglie_laiyuan = 0

                    if is_binglie_laiyuan == 2:  # 并列来源
                        top1 = [(0, loc_top[i0][0][1], loc_top[i0 + 1][0][0], loc_top[i0][0][3]), loc_top[i0][1]]
                        locname.append([top1, 0])

                        bottom1 = [(0, loc_bottom[j0][0][1], loc_top[i0 + 1][0][0], loc_bottom[j0][0][3]),
                                   loc_bottom[j0][1]]
                        locname.append([bottom1, 1])
                        max = loc_top[i0 + 1][0][0]
                        if max > loc_bottom[j0 + 1][0][0]:
                            max = loc_bottom[j0 + 1][0][0]
                        top2 = [(max, loc_top[i0 + 1][0][1], canvas_size[2], loc_top[i0 + 1][0][3]),
                                loc_top[i0 + 1][1]]
                        locname.append([top2, 0])

                        bottom2 = [(max, loc_bottom[j0 + 1][0][1], canvas_size[2], loc_bottom[j0 + 1][0][3]),
                            loc_bottom[j0 + 1][1]]

                        locname.append([bottom2, 1])
                        i0 += 2
                        j0 += 2
                    elif is_binglie_laiyuan == 1:  # 非并列来源
                        # 当前头部为i0,并列头部为i0+1,
                        # 如果只有一个来源（A），取这个来源的下一个来源（B），判断来源B和头部i0+2的关系
                        # 来源B
                        top1 = [(0, loc_top[i0][0][1], canvas_size[2], loc_top[i0 + 1][0][3]),
                                loc_top[i0][1] + loc_top[i0 + 1][1]]
                        locname.append([top1, 0])
                        bottom1 = [(0, loc_bottom[j0][0][1], canvas_size[2], loc_bottom[j0][0][3]),
                                   loc_bottom[j0][1] + loc_bottom[j0][1]]
                        locname.append([bottom1, 1])

                        i0 += 2
                        j0 += 1  # 此处为什么+1？
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

            '''
            将locname转为loc_named_pic
            '''
            while k <= len(locname) - 1:
                if k == 0 and locname[k][1] == 1:  # 第一行是表尾，定义x1，x2为pdf宽度，y1为pdf顶，y2为表尾坐标
                    x1 = canvas_size[0]
                    x2 = canvas_size[2]
                    y1 = canvas_size[3]
                    y2 = locname[0][0][0][3]
                    name = tmp
                    # loc_named_pic.append([name, (x1, y1, x2, y2)]) # 第一行是尾 忽略
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

                                if hasEnoughLength(locname[k][0][0][1], locname[ii][0][0][3]):
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

    def get_crops(self, pic_path, canvas_size, position, cropped_pic_name, cropped_pic_path,savepath,pic_name):
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

        x1 = max(position[0] - size_increase, 0) * (pic_size[0] / canvas_size[2])
        x2 = min(position[2] + size_increase, canvas_size[2]) * (pic_size[0] / canvas_size[2])
        y1 = max(0, (1 - (position[1] + size_increase) / canvas_size[3]) * pic_size[1])
        y2 = min(pic_size[1], (1 - (position[3] - size_increase) / canvas_size[3]) * pic_size[1])

        cropped_img = img.crop((x1, y1, x2, y2))
        cropped_pic_name = cropped_pic_name
        cropped_pic_name = cropped_pic_name.replace('/', '')
        cropped_pic_name = cropped_pic_name.replace('  ', '')
        cropped_pic_name = cropped_pic_name.replace('\\', '')
        #cropped_pic_name = cropped_pic_name.replace(':', '')
        cropped_pic_name = cropped_pic_name.replace('*', '')
        cropped_pic_name = cropped_pic_name.replace('?', '')
        cropped_pic_name = cropped_pic_name.replace('"', '')
        cropped_pic_name = cropped_pic_name.replace('<', '')
        cropped_pic_name = cropped_pic_name.replace('>', '')
        cropped_pic_name = cropped_pic_name.replace('|', '')
        cropped_pic_name = cropped_pic_name.replace('\n', '')
        cropped_pic_name = cropped_pic_name.replace('\r', '')
        #cropped_pic_name = cropped_pic_name.replace('\f', '')
        if len(cropped_pic_name) > 200:
            cropped_pic_name = cropped_pic_name[0:199]
        count += 1
        text0 = []
        log0 = []
        try:
            path = os.path.join(cropped_pic_path, str(pic_name)) + '.png'
            cropped_img.save(path)
            text0 = str(float('%.2f' % position[0])) + ',' + str(float('%.2f' % position[1])) + ',' + str(float('%.2f' % position[2])) + ',' + str(float('%.2f' % position[3])) + '|' + savepath + str(pic_name) + '.png' + '|' + cropped_pic_name
            return text0, log0
        except:
            log0 = cropped_pic_path + cropped_pic_name
            print('失败', cropped_pic_name)
            return text0, log0

    def main(self, pic_path, cropped_pic_path, pgn=None, tmp='',savepath='',pngnum=0):
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
        hasFindHengPng = 0

        if pgn is not None:
            # 获取当前页的doc
            doc_pdf = self.doc_pdfs[pgn]
            doc_pic = self.doc_pics[pgn]
            # 将当前页转换为PNG, 返回值为图片路径
            path = self.to_pic(doc_pic, 2, pgn, pic_path)
            loc_name_pic, canvas_size, tmp, topNumber, bottomNumber = self.get_pic_loc(doc_pdf, tmp=tmp)
            print('当前页码：' + str(pgn))
            if canvas_size[2] > canvas_size[3]:
                hasFindHengPng = 1

            if loc_name_pic:
                for i in loc_name_pic:
                    position = i[1]
                    cropped_pic_name = re.sub('/', '_', i[0])
                    if cropped_pic_name == '':
                        continue
                    pngnum += 1
                    text1, log1 = self.get_crops(path, canvas_size, position, cropped_pic_name, cropped_pic_path,savepath,pngnum)
                    if text1:
                        text1 = str(pgn) + '|' + text1
                        text_total.append(text1)

                        ##写入文件

                    if log1:
                        log1 = log1 + '|第' + str(pgn) + '页出错'
                        log_total.append(log1)
                        continue
        return tmp, text_total, log_total, topNumber, bottomNumber, hasFindHengPng,pngnum

def run(pic_path0, cropped_pic_path0, text_dir, file_dir,is_only_today):
    import warnings
    import time
    time_start = time.time()
    log_total1 = []
    #定义字典 用来存放日文件夹中文件夹个数(key值：20190919)
    files_count_dict = {'20000101': 0, '30001231': 0}
    
    for files in os.walk(file_dir):
        #文件夹截取前4位排序
        files[1].sort(reverse=True,key=lambda x: x[0:4])
        #判断是否为处理当天数据
        if is_only_today == str(1):
            today = time.strftime('%Y_%m_%d', time.localtime(time.time()))
            if files[0].endswith(today):
                print(today)
            else:
                continue

        for pdf_name in files[2]:
            #判断是否为pdf文件
            if pdf_name[-3:] == 'pdf':
                #*****************************************新文件夹名称以及文件对应文件夹顺序名称
                #START**************************************************
                #获取文件全部路径
                full_path = os.path.join(files[0], pdf_name)
                #获取文件修改时间，未格式化
                mtime = os.stat(full_path).st_mtime
                #存放路径 月
                file_modify_time_month = time.strftime('%Y%m', time.localtime(mtime))
                #存放路径 日
                file_modify_time_day = time.strftime('%d', time.localtime(mtime))
                #拼接路径
                file_save_path = str(file_modify_time_month) + '\\' + str(file_modify_time_day) + '\\'

                #查看字典中是否存在该天数据
                if str(file_modify_time_day) in files_count_dict:
                    files_count_dict[str(file_modify_time_day)] = files_count_dict[str(file_modify_time_day)] + 1
                else:
                    #查看该天文件夹中文件总数，总文件数加1
                    files_totle = 0
                    for get_files_count in os.walk(cropped_pic_path0 + file_save_path):
                        #判断是否有值
                        if len(get_files_count[1]) > 0:
                            #获取最大数字的值
                            files_totle = max(map(int,get_files_count[1]), key=abs)
                    files_count_dict[str(file_modify_time_day)] = files_totle + 1
                    
                #*****************************************新文件夹名称以及文件对应文件夹顺序名称
                #END**************************************************
                #txt保存文件内容存放
                text_total1 = []
                #打印数据
                pdf_path = files[0] + '\\' + pdf_name
                print(pdf_path)

                 #txt文件存放文件夹名称
                path_file_p = text_dir + file_save_path

                #txt文件路径带名称
                path_file_name = path_file_p + pdf_name[:-4] + '.txt'

                #判断txt对应文件夹与文件是否存在
                if not os.path.exists(path_file_p):
                    os.makedirs(path_file_p)
                if os.path.exists(path_file_name):
                    print('当前文件已存在')
                    #如果存在判断带下划线的文件,如果都不存在,则创建一个带下划线的同名文件,再有不需要管  暂时有问题（如果重新运行，全部都是重复的，需要全部重新生成）
                    continue
                
                #图片保存路径
                cropped_pic_path = cropped_pic_path0 + file_save_path + str(files_count_dict[str(file_modify_time_day)])
                #判断图片保存文件夹是否存在
                if not os.path.exists(cropped_pic_path):
                    os.makedirs(cropped_pic_path)

                #中间截图:图片保存路径
                pic_path = pic_path0 + file_save_path + str(files_count_dict[str(file_modify_time_day)])
                #中间截图:判断图片保存文件夹是否存在
                if not os.path.exists(pic_path):
                    os.makedirs(pic_path)

                tmp = ''

                try:
                    test = GetPic(pdf_path)
                    page_count = test.doc_pics.pageCount
                    findAllTopNumber = 0
                    findAllBottomNumber = 0
                    pngnum = 0
                    for i in range(page_count):
                        try:
                            tmp, text_total, log_total, topNumber, bottomNumber, hasFind,pngnum = test.main(pic_path,
                                                                                                     cropped_pic_path,
                                                                                                     pgn=i,
                                                                                                     tmp=tmp,
                                                                                                     savepath=str(file_modify_time_month) + '/' + str(file_modify_time_day) + '/' + str(files_count_dict[str(file_modify_time_day)]) + '/',
                                                                                                     pngnum=pngnum)#savepath 月/日/文件排序名/

                            if hasFind == 1:  # 横版的暂时屏蔽了
                                break

                            findAllTopNumber = findAllTopNumber + topNumber
                            findAllBottomNumber = findAllBottomNumber + bottomNumber

                            if text_total:
                                for text1 in text_total:
                                    text_total1.append(text1)
                            if log_total:
                                for log1 in log_total:
                                    log_total1.append(log1)                            
                        except:
                            log_total1.append(pdf_path + '第' + str(i) + '页出错')
                    #打印每篇文章完成有多少图
                    print(pdf_name[:-4] + '完成：共' + str(pngnum) + '图')
                    #删除临时文件夹
                except:
                    log_total1.append(pdf_path + '\\' + pdf_name[:-4] + '不是pdf')

                finally:
                    if text_total1:
                        try:
                            with open(path_file_name, "w",encoding='utf-8') as f:
                                #cop =
                                #re.compile("[^\u4e00-\u9fa5^a-z^A-Z^0-9^\s^.^:^|^,]")
                                #去掉非中英文字符
                                for i in text_total1:
                                    #i = cop.sub('', i)
                                    i = i + '\n'
                                    f.write(i)
                        except:
                            path_file_name = cropped_pic_path + '\\data_list.txt'
                            with open(path_file_name, "w",encoding='utf-8') as f:
                                f.write('no data')

                    else:
                        path_file_name = cropped_pic_path + '\\data_list.txt'
                        with open(path_file_name, "w",encoding='utf-8') as f:
                            f.write('no data')
        log_file_name = text_dir + 'log' + '.txt'
        isExists = os.path.exists(text_dir)
        if not isExists:
            os.makedirs(text_dir)
        time_end = time.time()
        with open(log_file_name, "a+",encoding='utf-8') as f:
            for i in log_total1:
                f.write(i + '\n')
            f.write('\n'+file_dir+'|运行时间' + str(time_end - time_start))


def hasEnoughLength(y1, y2):
    '''
        :param y1:  表头的底部y坐标
        :param y2:  表尾的顶部y坐标
        :return: 是否足够长
    '''
    return y1 > y2 + 20


if __name__ == '__main__':
   

    while 1:
        #配置文件路径
        setting_path = 'f:\\PDFCutOut\\setting\\setting.ini'
        isExistsSetting = os.path.exists(setting_path)
        if not isExistsSetting:
            import warnings
            warnings.filterwarnings("ignore")
            log_total1 = []
            file_dir = 'e:\\pdfreport\\upfile\\'
            pic_path0 = 'f:\\PDFCutOut\\pic_txt\\pic_path\\'
            cropped_pic_path0 = 'f:\\PDFCutOut\\pic_txt\\cropped_pic_path\\'
            text_dir = 'f:\\PDFCutOut\\pic_txt\\text\\'
        else:
            cfg = ConfigParser()
            config = ConfigParser()
            config.read(setting_path)
            file_dir = config.get("SETTING","file_dir")
            pic_path0 = config.get("SETTING","pic_path")
            cropped_pic_path0 = config.get("SETTING","cropped_pic_path")
            text_dir = config.get("SETTING","text_dir")
            is_only_today = config.get("SETTING","is_only_today")
        
        try:
            run(pic_path0, cropped_pic_path0, text_dir, file_dir,is_only_today)
        except Exception as e:
            log_file_name=text_dir + 'log' + '.txt'
            isExists = os.path.exists(text_dir)
            if not isExists:
                os.makedirs(text_dir)
            with open(log_file_name, "a+",encoding='utf-8') as f:
                f.write('\n程序运行出错|'+file_dir+'|' + str(e))
        print('我要休眠5分钟，等待新的报告')
        time.sleep(5*60)
'''
##外部传参
file_dir pdf目录
pic_path pic目录
cropped_pic_path 截图目录
'''
