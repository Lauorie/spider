import re
import sqlite3
import urllib.request
import xlwt
from bs4 import BeautifulSoup


def main():
    baseurl = "https://movie.douban.com/top250?start="
    # 1.爬取网页
    datalist = getData(baseurl)
    # savepath = "豆瓣电影TOP250.xls"    # 以excel的方式保存
    dbpath = "moive.db"
    # 3.保存数据
    # saveData(datalist, savepath)
    saveData2DB(datalist, dbpath)
    # askURL("https://movie.douban.com/top250?start=")

# 影片详情的链接的规则
findLink = re.compile(r'<a href="(.*?)">')  # 创建正则表达式规则，表示规则（字符串的模式）
# 影片图片
findImgSrc = re.compile(r'<img.*src="(.*?)"', re.S)  # re.S让换行符包含在字符串中
# 影片片名
findTitle = re.compile(r'<span class="title">(.*)</span>')
# 影片评分
findRating = re.compile(r'<span class="rating_num" property="v:average">(.*)</span>')
# 评价人数
findJudge = re.compile(r'<span>(\d*)人评价</span>')
# 找到概况
findInq = re.compile(r'<span class="inq">(.*)</span>')
# 找到影片相关内容
fingBd = re.compile(r'<p class="">(.*?)</p>', re.S)

# 爬取网页
def getData(baseurl):
    datalist = []
    for i in range(0, 10):  # 调用获取信息的函数10词
        url = baseurl + str(i*25)
        html = askURL(url)   # 保存获取到的网页源码
        # 2.逐一解析数据
        soup = BeautifulSoup(html, "html.parser")
        for item in soup.find_all("div", class_="item"):  # 查找符合要求的字符串，形成列表，class要加下划线
            # print(item)  # 测试查看电影item全部信息
            data = []  # 保存一部电影的所有信息
            item = str(item)

            # 影片详情的链接
            link = re.findall(findLink, item)[0]  # re库用来通过正则表达式查找指定的字符串，[0]只需要找到的第一个即可
            data.append(link)                     # 添加链接

            imgSrc = re.findall(findImgSrc, item)[0]
            data.append(imgSrc)                   # 添加图片

            titles = re.findall(findTitle,item)   # 片名可能只有一个中文名，没有外国名的情况，要加if判断
            if len(titles) == 2:
                ctitle = titles[0]                # 添加中文名
                data.append(ctitle)
                otitle = titles[1].replace("/", "")  # 替换掉外文名前面的/
                data.append(otitle)               # 添加外文名
            else:
                data.append(titles[0])
                data.append(" ")                  # 外文名留空，保证excel格式正确

            rating = re.findall(findRating, item)[0]
            data.append(rating)                   # 添加评分

            judgeNum = re.findall(findJudge, item)[0]
            data.append(judgeNum)                 # 添加评分人数

            inq = re.findall(findInq, item)       # 概况有不存在的情况出现，所以要加判断
            if len(inq) != 0:
                inq = inq[0].replace("。", "")    # 去掉里面的句号
                data.append(inq)                  # 添加概述
            else:
                data.append(" ")                   # 没有的话就留空


            bd = re.findall(fingBd, item)[0]
            bd = re.sub('<br(\s+)?/>(\s+)?', " ", bd)   # 去掉<br/> 及br里面包含的一些内容
            bd = re.sub('/', " ", bd)              # 将/替换为空格
            data.append(bd.strip())                # 去除前面处理完剩余的许多空白

            datalist.append(data)                  # 把处理好的一部电影信息存入datalist
    # for a in datalist[0]:                        # 可以先打印一部出来看一下格式
    #     print(a)
    return datalist

# 得到一个指定URL的网页内容
def askURL(url):
    head =  {
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
}
    request = urllib.request.Request(url,headers=head)  # 封装信息
    html = ""
    try:
        response = urllib.request.urlopen(request)
        html = response.read().decode("utf-8")
        # print(html)
    except urllib.error.URLError as e: # 如果出错，打印出错类型
        if hasattr(e, "code"):
            print(e.code)
        if hasattr(e, "reason"):
            print(e.reason)
    return html



# 保存数据
def saveData(datalist, savepath):
    print("save...")
    book = xlwt.Workbook(encoding="utf-8", style_compression=True)       # 创建workbook对象
    sheet = book.add_sheet("豆瓣电影TOP250", cell_overwrite_ok=True)      # 创建工作表,覆盖掉此前的内容
    col = ["电影详情链接", "图片链接", "影片中文名", "影片外文名", "评分", "评价人数", "概况", "相关信息"]
    for i in range(0, 8):
        sheet.write(0, i, col[i])
    for item in range(0, 250):
        print("第%d条" % (item+1))
        data = datalist[item]
        for j in range(0, 8):
            sheet.write(item+1, j, data[j])                                # 写入数据，worksheet.write(行, 列, "值")
    book.save(savepath)                                                 # 保存数据表

def saveData2DB(datalist, dbpath):
    inti_db(dbpath)
    conn = sqlite3.connect(dbpath)
    cur = conn.cursor()
    for data in datalist:
        for index in range(len(data)):
            if index == 4 or index == 5:              # 第5和4是numeric不是字符串型
                continue
            data[index] = '"' + data[index] + '"'    # 把它变成字符串模式便于添加进sql
        sql = """
                insert into movie250(
                info_link, pic_link, cname, ename, score, rated, introduction, info)
                values (%s)"""%",".join(data)
        # 三个点是分行写一个语句，但为什么最后三个点，不是放在最后面，却放在了中间那
        print(sql)
        cur.execute(sql)
        conn.commit()
    cur.close()
    conn.close()

def inti_db(dbpath):
    sql = """
    create table movie250
    (id integer primary key autoincrement,
    info_link text,
    pic_link text,
    cname varchar,
    ename varchar,
    score numeric,
    rated numeric,
    introduction text,
    info text
    )
    """       # 创建数据表
    conn = sqlite3.connect(dbpath)    # 如果地址存在则打开表，如果不存在就创建一个数据表
    cursor = conn.cursor()            # 创建游标
    cursor.execute(sql)               # 执行sql
    conn.commit()                     # 提交数据库操作
    conn.close()


if __name__ == "__main__":  # 当程序执行时
    # 调用函数
    main()
    # inti_db('movietest.db')   # 查看数据库是否创建成功
    print("爬取完毕！")