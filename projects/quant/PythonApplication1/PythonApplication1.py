import base64
import datetime
import html
import json
import os
import random
import re
import time
import urllib

from bs4 import BeautifulSoup
import requests


cur_dir = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(cur_dir, 'config.json')

config = {}
with open(config_file, 'r', encoding='utf8') as f:
    config = json.load(f)

if not config['output_dir']:
    config['output_dir'] = os.path.join(cur_dir, 'output')
if not os.path.exists(config['output_dir']):
    os.makedirs(config['output_dir'])
record_file = os.path.join(config['output_dir'], 'record.txt')

# 设置一个记录，用于断点续抓。如果需要重抓，删除记录即可
records = set()
if os.path.exists(record_file):
    with open(record_file, 'r', encoding='utf8') as f:
        records = set(line.rstrip('\n') for line in f)

# 只处理以下消息类型： 49 为普通图文类型，其他类型跳过
ALLOWED_MSG_TYPE = [49, ]

re_comment_id = re.compile(r'\n\s*var +comment_id *= *[^\n]*[\'\"](\d+)[\'\"]')
re_appmsgid = re.compile(r'\n\s*var +appmsgid *= *[^\n]*[\'\"](\d+)[\'\"]')
re_appmsg_token = re.compile(r'\n\s*var +appmsg_token *= *[^\n]*[\'\"](\.+)[\'\"]')
re_devicetype = re.compile(r'\n\s*var +devicetype *= *[^\n]*[\'\"](.+)[\'\"]')
re_clientversion = re.compile(r'\n\s*var +clientversion *= *[^\n]*[\'\"](\d+)[\'\"]')
re_uin = re.compile(r'\n\s*window\.uin *= *[^\n]*[\'\"]([\w=\%]+)[\'\"]')
re_key = re.compile(r'\n\s*window\.key *= *[^\n]*[\'\"]([\w=\%]+)[\'\"]')
re_wxtoken = re.compile(r'\n\s*window\.wxtoken *= *[^\n]*[\'\"]([\w=\%]+)[\'\"]')


# 文章类
class Article(object):
    def __init__(self, id, datetime, title, author, digest, cover_url, content_url, source_url, content=None, index=0):
        self.id = id
        self.datetime = datetime
        self.title = title
        self.author = author
        self.digest = digest
        self.cover_url = cover_url
        self.content_url = content_url
        self.source_url = source_url
        self.content = content
        # index 为 0 表示头条文章，次条文章编号依次递增
        self.index = index

    def __getitem__(self, key):
        return getattr(self, key)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return f'<Article {self.__dict__}>'


def parse_fiddler_export(input_dir):
    """解析 Fiddler 导出的文章列表文件，得到文章列表。
    历史文章列表一般以 json 文件保存，可直接载入并解析。
    但有个特例：home 页的列表保存在 html 内的一段脚本中，需要单独提取。
    """
    for filename in sorted(os.listdir(input_dir)):
        ext = os.path.splitext(filename)[-1].lower()
        if ext not in ('.html', '.htm', '.json'):
            continue

        file = os.path.join(input_dir, filename)
        with open(file, 'r', encoding='utf8') as f:
            content = f.read()

        # 解析 home 页 html 文件，获得首屏文章列表
        if ext in ('.html', '.htm'):
            pattern = r'\n\s*var +msgList *= *[\'\"](\{[^\n]+\})[\'\"] *; *\n'
            json_str = re.search(pattern, content).group(1)
            # 原始字符串中包含 &nbsp; &quote; &amp; 等转移字符，需要解转义。
            json_str = html.unescape(json_str)
            obj = json.loads(json_str)
            msg_list = obj['list']

        # 解析翻页 json 文件，获得后续历史文章列表
        elif ext == '.json':
            obj = json.loads(content)
            msg_list = json.loads(obj['general_msg_list'])['list']

        for msg in msg_list:
            if msg['comm_msg_info']['type'] not in ALLOWED_MSG_TYPE:
                continue
            article = Article(
                msg['comm_msg_info']['id'],
                msg['comm_msg_info']['datetime'],
                msg['app_msg_ext_info']['title'],
                msg['app_msg_ext_info']['author'],
                msg['app_msg_ext_info']['digest'],
                msg['app_msg_ext_info']['cover'],
                msg['app_msg_ext_info']['content_url'],
                msg['app_msg_ext_info']['source_url'],
                )
            article.datetime = datetime.datetime.fromtimestamp(article.datetime)
            yield article

            # 有些消息包含多篇文章，此处解析次条
            if msg['app_msg_ext_info']['is_multi']:
                for idx, sub_msg in enumerate(msg['app_msg_ext_info']['multi_app_msg_item_list']):
                    article = Article(
                        msg['comm_msg_info']['id'],
                        msg['comm_msg_info']['datetime'],
                        sub_msg['title'],
                        sub_msg['author'],
                        sub_msg['digest'],
                        sub_msg['cover'],
                        sub_msg['content_url'],
                        sub_msg['source_url'],
                        index=idx + 1,
                        )
                    article.datetime = datetime.datetime.fromtimestamp(article.datetime)
                    yield article


def article_pipe(article_iter):
    """对文章列表进一步处理。
    包括处理元信息（主要是对 url 解转义），按照时间、文章次序排序等。
    """
    article_list = []
    for article in article_iter:
        for attr in ('cover_url', 'content_url', 'source_url'):
            new_url = html.unescape(getattr(article, attr)).replace(r'\/', '/')
            setattr(article, attr, new_url)
        article_list.append(article)

    article_list.sort(key=lambda article: (article.datetime, article.index))
    return article_list


def get_comments(article, base_params, session):
    """从文章的 content_url 和 content 中解析相关参数，构造请求评论的 URL，最终获得评论数据

    文章接口示例：https://mp.weixin.qq.com/s?__biz=MzAwMzU1ODAwOQ==&mid=2650332778&idx=1&sn=4acfcb69e9b63eec3efc4a9d94cc6cad&chksm=8335217cb442a86a61c8c3321e3741b7d7d6e28f9357d0a27f4353bf7a7896cae584bbc14387&scene=27#wechat_redirect
    评论接口示例：https://mp.weixin.qq.com/mp/appmsg_comment?action=getcomment&scene=0&__biz=MzAwMzU1ODAwOQ==&appmsgid=2650332982&idx=1&comment_id=1054388621538770944&offset=0&limit=100&uin=MjI5MDQwNTIzNg%253D%253D&key=90610e7a4a02526ca52f96868014fc10dc52f9f6c531f3bbf72541688a88014ffd7682ec315b7d6434b87938f8b87c741aa41d31f90f951648a409365cef63aba4ec76ad21e3d671d09df460e17e87a5&pass_ticket=nQePwVT9BEpY%25252FozZHsy33LGDMUCXfgbCMKZTPCnDslELz4XHZ2AEXZVpKpF0yEeH&wxtoken=777&devicetype=Windows%26nbsp%3B10&clientversion=62070152&__biz=MzAwMzU1ODAwOQ%3D%3D&appmsg_token=1033_3iubBoXR%252F6I0xBAcSf2BpR9hk5tm6g5v3GSvo2wyPqnN7rYBSNgdvpjxA02o_wy57E25IktRF_ugMLDP&x5=0&f=json
    """
    content_url_params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(article.content_url).query))

    m_comment_id = re.search(re_comment_id, article.content)
    m_uin = re.search(re_uin, article.content)
    m_key = re.search(re_key, article.content)
    m_wxtoken = re.search(re_wxtoken, article.content)
    m_devicetype = re.search(re_devicetype, article.content)
    m_clientversion = re.search(re_clientversion, article.content)
    m_appmsg_token = re.search(re_appmsg_token, article.content)

    comment_url = 'https://mp.weixin.qq.com/mp/appmsg_comment'
    params = {
        'action': 'getcomment',
        'scene': 0,
        '__biz': base_params['__biz'],
        'appmsgid': content_url_params['mid'],
        'idx': content_url_params['idx'],
        'comment_id': (m_comment_id and m_comment_id.group(1)) or '',
        'offset': 0,
        'limit': 100,
        'uin': base_params.get('uin') or (m_uin and m_uin.group(1)) or '',
        'key': base_params.get('key') or (m_key and m_key.group(1)) or '',
        'wxtoken': base_params.get('wxtokenkey') or (m_wxtoken and m_wxtoken.group(1)) or '',
        'pass_ticket': base_params['pass_ticket'],
        'devicetype': (m_devicetype and m_devicetype.group(1)) or '',
        'clientversion': (m_clientversion and m_clientversion.group(1)) or '',
        'appmsg_token': base_params.get('appmsg_token') or (m_appmsg_token and m_appmsg_token.group(1)) or '',
        'x5': 0,
        'f': 'json',
    }
    response = session.get(comment_url, params=params)
    print(f'调试评论拉取接口：{response.request.url}')
    obj = response.json()
    comments = [
        {
            'nick_name': comm['nick_name'],
            'logo_url': comm['logo_url'],
            'content': comm['content'],
            'create_time': comm['create_time'],
            'like_num': comm['like_num'],
            'reply': None if not comm['reply']['reply_list'] else comm['reply']['reply_list'][0],
        }
        for comm in obj.get('elected_comment', [])]
    return comments


def _create_comment_html(comments):
    """构建具有微信样式的评论区 html"""

    if not comments:
        return ''

    comments_area = BeautifulSoup('''
        <div><style>
            .comment_block {
                position: relative;
                margin-bottom: 25px;
                font-size: 0.9em;
            }
            .logo_block {
                position: absolute;
                left: 0;
                width: 40px;
                padding-right: 5px;
                box-sizing: border-box;
            }
            .logo_block img {
                width: 100%;
            }
            .comment_meta {
                position: relative;
                margin-left: 40px;
                color: #999;
                font-size: 0.9em;
                height: 1.2em;
                line-height: 1em;
            }
            .comment_meta span {
                display: inline-block;
                position: absolute;
            }
            .comment_content {
                margin-left: 40px;
                margin-bottom: 5px;
                clear: both;
                line-height: 1.5em;
            }
        </style></div>
        ''', features='lxml')

    for comm in comments:
        reply_div = ''
        if comm['reply']:
            reply_div = f'''
                <div class="comment_meta" style="border-left: solid 3px #1AAD19;">
                    <span style="left: 0; padding-left: 5px;">作者</span>
                    <span style="right: 0">👍 {comm['reply'].get('reply_like_num', 0)}</span>
                </div>
                <div class="comment_content">{comm['reply']['content']}</div>
            '''
        comm_div = BeautifulSoup(f'''
            <div class="comment_block">
                <div class="logo_block"><img src="{comm['logo_url']}"/></div>
                <div class="comment_meta">
                    <span style="left: 0">{comm['nick_name']}</span>
                    <span style="right: 0">👍 {comm['like_num']}</span>
                </div>
                <div class="comment_content">{comm['content']}</div>
                {reply_div}
            </div>
            ''', features='lxml')
        comments_area.append(comm_div)

    return comments_area


def modify_content(article, comments, session):
    """原地修复文章内容：清理无关标签、嵌入图片、添加发布时间、添加评论信息等"""
    soup = BeautifulSoup(article.content, features='lxml')

    # 清理不必要的标签
    for tag in soup.find_all('script'):
        tag.decompose()

    # 将图片以 base64 编码嵌入到 html 文件中
    for img in soup.find_all('img'):
        url = img.attrs.get('data-src') or img.attrs.get('src')
        if not url:
            continue
        if url.startswith('//'):
            url = 'http:' + url
        img_type = img.attrs.get('data-type') or 'png'

        response = session.get(url)
        b64 = base64.b64encode(response.content).decode('ascii')
        img['src'] = f'data:image/{img_type};base64,{b64}'

    # 添加发布时间
    tag = soup.find(id='publish_time')
    if tag:
        tag.string = article.datetime.strftime('%Y-%m-%d %H:%M:%S')

    # 将评论内容追加到 html 文档末尾
    comments_area = _create_comment_html(comments)
    if comments_area:
        tag = soup.find(class_='rich_media_area_primary_inner')
        if not tag:
            tag = soup.body
        tag.append(comments_area)
    new_content = soup.prettify()
    article.content = new_content


def parse_raw_http_request(request_text):
    """解析从 Fiddler 中导出的 HTTP 请求文本，用于获取请求参数、cookie 等字段"""
    from http.server import BaseHTTPRequestHandler
    from io import BytesIO

    class HTTPRequest(BaseHTTPRequestHandler):
        def __init__(self, request_text):
            self.rfile = BytesIO(request_text)
            self.raw_requestline = self.rfile.readline()
            self.error_code = self.error_message = None
            self.parse_request()

        def send_error(self, code, message):
            self.error_code = code
            self.error_message = message

    request = HTTPRequest(request_text)
    return request


def parse_raw_cookie(cookie_str):
    """将原始 cookie 字符串解析为 dict"""
    from http.cookies import SimpleCookie

    cookie = SimpleCookie()
    cookie.load(cookie_str)
    cookie = {key: morsel.value for key, morsel in cookie.items()}
    return cookie


def valid_filename(name):
    """转义某些字符，使字符串成为合法的文件名。
    在Windows中，/ \ : * ? " ' < > | 这几个字符不能存在于文件夹名或文件名中，替换为下划线。
    """
    new_name = re.sub(r'[\/\\\:\*\?\"\'\<\>\|]', '_', name)
    return new_name


def main():
    with open(os.path.join(config['input_dir'], config['raw_request']), 'rb') as f:
        raw_request = f.read()
    request = parse_raw_http_request(raw_request)

    common_headers = {
        'User-Agent': request.headers['User-Agent'],
        'Accept': request.headers['Accept'],
        'Connection': request.headers['Connection'],
        'Accept-Language': request.headers['Accept-Language'],
    }

    # 解析请求参数与 Cookies，留待稍候使用
    params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(request.path).query))
    cookies = parse_raw_cookie(request.headers['cookie'])
    params.update(cookies)

    with requests.Session() as session:
        session.headers.update(common_headers)
        session.cookies.update(cookies)

        for article in article_pipe(parse_fiddler_export(config['input_dir'])):
            # 跳过内容为空的文章
            if not article.content_url:
                continue

            fingerprint = f'{article.datetime:%Y%m%d}-{article.title}'
            print('-' * 80)
            print(fingerprint)

            # 忽略已经抓取过的文章
            if fingerprint in records:
                print(f'文章已在抓取记录中，忽略')
                continue

            # 忽略次条中包含原文链接的文章，一般是广告
            if article.index > 0:
                print(f'该文章为次条文章，编号 {article.index}')
                if article.source_url.strip():
                    print('该文章很可能为推广文章，忽略')
                    continue

            print(article)
            article.content = session.get(article.content_url).text

            # with open('tmp.html', 'w', encoding='utf8') as f:
            #     f.write(article.content)

            comments = get_comments(article, params, session)
            print(f'文章包含 {len(comments)} 条评论。示例：{comments[:1]}')
            modify_content(article, comments, session)

            filename = f'{article.datetime:%Y%m%d}-{article.index+1:02d}-{article.title}.html'
            filename = valid_filename(filename)
            with open(os.path.join(config['output_dir'], filename), 'w', encoding='utf8') as f:
                f.write(article.content)

            # 抓取完成，将文章加入记录
            records.add(fingerprint)
            with open(record_file, 'a', encoding='utf8') as f:
                f.write(fingerprint + '\n')

            time.sleep(random.random() * 5)


if __name__ == '__main__':
    main()