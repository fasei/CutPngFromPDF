import os
import random

from PIL import Image
import re

'''
查找横版图片
'''


def canNextStep(maxFileNumber, tempMaxSameNum, maxSameNum):
    '''
    :param maxFileNumber:  最大的文件数量
    :param tempMaxSameNum:  当前相同的最大数量
    :param maxSameNum:  全局最大数量
    :return:
    '''

    if tempMaxSameNum >= maxSameNum:  # 如果当前的和全局的相同，直接下一步
        return True
    else:
        if maxFileNumber <= 5:  # 总页数小于3页时，就不比较了
            return False
        else:  # 总页数大于5页时，特殊处理一下
            if tempMaxSameNum >= maxFileNumber * 0.8:  # 正确率为80%
                if maxSameNum - tempMaxSameNum <= 3:  # 与正确的最大相同页数不能相差太多，暂定为3
                    return True
                else:
                    return False
            else:
                return False


def readImgWithSize():
    '''
    按照文件大小判断页眉

    :return:
    '''
    log_total1 = []
    # file_di r ='e:\\pdfreport\\upfile\\'
    pic_path0 = 'e:\\pdfreport\\t\\pic_path\\'
    cropped_pic_path0 = 'e:\\pdfreport\\t\\cropped_pic_path\\'
    # text_di r ='e:\\pdfreport\\t\\text\\'

    test_cropped_pic_path0 = 'd:\\pdfreport\\t\\pic_path\\77181642\\'

    startTime = time.time()

    picHeight = 0;  # 当前目录一张图片高度
    tempHeaderHeight = 0  # 初始高度，逐渐增大，获取到第一张图片是初始化高度
    maxSameNum = 0  # 最大相同数字

    for i in range(1000):
        print('开始尝试了，这是第' + str(i + 1) + '次')
        # 筛选出最合适的头部高度
        tempMaxSameNum = 0  # 最大相同数字
        maxFileNumber = 0
        for files in os.walk(test_cropped_pic_path0):
            allSize = []
            # print(files)
            maxFileNumber = 0
            for pdf_name in files[2]:
                if pdf_name.startswith('0.png'):  # 第一张图片不管，封面图太乱了
                    continue

                if pdf_name.startswith('temp'):  # 临时无用的图片文件
                    continue
                # 操作的图片名称为1.png......n.png
                maxFileNumber = maxFileNumber + 1
                # print(pdf_name)
                img = Image.open(test_cropped_pic_path0 + pdf_name)  # 打开当前路径图像
                width = img.size[0]
                height = img.size[1]
                picHeight = height

                if tempHeaderHeight == 0:  # 初始化默认最小高度
                    tempHeaderHeight = (int)(width / 15)  # 初始高度，逐渐增大

                box1 = (0, 0, width, tempHeaderHeight)  # 设置图像裁剪区域 (x左上，y左上，x右下,y右下)
                image1 = img.crop(box1)  # 图像裁剪
                saveTempFilePath = test_cropped_pic_path0 + 'temp_header_' + pdf_name
                image1.save(saveTempFilePath)  # 存储裁剪得到的图像

                fileSize = os.path.getsize(saveTempFilePath)  # 获取缓存文件的大小
                allSize.append(fileSize)

            print(allSize)
            for j in range(len(allSize)):
                sameNum = 0
                ele = allSize[j]
                for n in allSize:
                    if n == ele:
                        sameNum = sameNum + 1
                if sameNum > tempMaxSameNum:
                    tempMaxSameNum = sameNum

            print('最大相同的有：' + str(tempMaxSameNum))
        if maxSameNum == 0:  # 初始化时操作
            maxFileNumber = tempMaxSameNum

        if canNextStep(maxFileNumber, tempMaxSameNum, maxSameNum):  # 最少保证三页是相同的
            maxSameNum = tempMaxSameNum
            tempHeaderHeight = tempHeaderHeight + 1  # 能找到更大的值，继续尝试
        else:
            tempHeaderHeight = tempHeaderHeight - 1
            break

        # if tempMaxSameNum >= maxSameNum:
        #     maxSameNum = tempMaxSameNum
        #     tempHeaderHeight = tempHeaderHeight + 1  # 能找到更大的值，继续尝试
        # else:
        #     tempHeaderHeight = tempHeaderHeight - 1
        #     break

    print('我筛选出的最大的头部高度为：' + str(tempHeaderHeight))

    endTime = time.time()
    print('运行时间为：' + str(endTime - startTime) + '秒')


if __name__ == '__main__':
    import time

    # test_cropped_pic_path0 = 'D:\\pdfreport\\self\\pic_path'
    test_cropped_pic_path0 = 'D:\\pdfreport\\t\\pic_path'

    log_path = 'e:\\logssss\\'

    errorFileName = log_path + '666_log' + '.txt'
    isExists = os.path.exists(log_path)
    import shutil

    if isExists:
        shutil.rmtree(log_path)
    os.makedirs(log_path)
    with open(errorFileName, "a+") as f:
        f.write('查找横版文件的目录：' + test_cropped_pic_path0 + '\n')

    startTime = time.time()
    findFile = 0

    for files in os.walk(test_cropped_pic_path0):
        allSize = []
        maxFileNumber = 0
        for pdf_name in files[2]:
            print(pdf_name)
            if pdf_name.startswith('0.png'):
                img = Image.open(files[0] + '\\' + pdf_name)  # 打开当前路径图像
                width = img.size[0]
                height = img.size[1]

                if width < height:
                    break
                else:
                    findFile += 1
                    print('width:', width, ',height:', height)
                    with open(errorFileName, "a+") as f:
                        f.write('文件路径：' + files[0] + '\n')
                    break

    # if tempMaxSameNum >= maxSameNum:
    #     maxSameNum = tempMaxSameNum
    #     tempHeaderHeight = tempHeaderHeight + 1  # 能找到更大的值，继续尝试
    # else:
    #     tempHeaderHeight = tempHeaderHeight - 1
    #     break

    endTime = time.time()
    print('查找到的文件夹数量为：' + str(findFile) + '个')
    print('运行时间为：' + str(endTime - startTime) + '秒')

'''
            for files in os.walk(test_cropped_pic_path0):
                count0 = 0
                for pdf_name in files[2]:
                    if pdf_name.startswith('temp_header_'):  # 临时无用的图片文件


                        print("666")
'''

#   file_dir= 'e:\\2\\'
# run(pic_path0 ,cropped_pic_path0 ,text_dir ,file_dir)
