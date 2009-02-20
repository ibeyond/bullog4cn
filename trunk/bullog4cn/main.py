# encoding=utf-8
import wsgiref.handlers
import logging
from google.appengine.ext import webapp
from google.appengine.api import urlfetch
from google.appengine.api import memcache

#远程主机，如果想代理其他主机的话。。。。。
remote_host = 'http://www.bullogger.com/'
#此处只是为了搞一下牛博的favicon，因为不是默认位置，而很多浏览器都会去默认位置去找，看appspot的后台有404让我觉得很不爽。
remote_favicon = remote_host + 'App_Themes/p_portal/images/shortcut.ico'

#google分析代码，自己看着办。
google_analytics = """
<script type="text/javascript">
var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
document.write(unescape("%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E"));
</script>
<script type="text/javascript">
try {
var pageTracker = _gat._getTracker("UA-7275846-1");
pageTracker._trackPageview();
} catch(err) {}</script>
"""

class MainPage(webapp.RequestHandler):
    
    def get(self):

        uri = self.request.uri
        url_list = uri.split('/')
        if uri == self.request.scheme + '://' + self.request.host + '/favicon.ico':
            url = remote_favicon
        else:
            url = (remote_host + '/'.join(url_list[3:]))
        try:
            #memcache.flush_all()
            result = memcache.get(url)
            if result is not None:
                #如果是图片，重定向到http方式，节省点ssl的流量。
                if result.headers['Content-Type'].find('image') != -1 and uri.find('https://') != -1:
                    self.redirect(uri.replace('https://','http://'))
                self.response.headers['Content-Type'] = result.headers['Content-Type']
                self.response.out.write(result.content)
                return
            result = urlfetch.fetch(url=url,headers=self.request.headers,allow_truncated=True)
            if result.status_code == 200:
                #不知道牛博为什么有时候会返回wap格式。
                if result.headers['Content-Type'] == 'text/vnd.wap.wml; charset=utf-8':
                    result.headers['Content-Type'] = 'text/html; charset=utf-8'
                self.response.headers['Content-Type'] = result.headers['Content-Type']
                if result.headers['Content-Type'].find('text/html') == -1:
                    try:
                        #非html内容，先Cache一天再说，当然，主要是图片
                        memcache.add(url,result,86400)
                    except:
                        pass
                    #如果是图片，重定向到http方式，节省点ssl的流量。
                    if result.headers['Content-Type'].find('image') != -1 and uri.find('https://') != -1:
                        self.redirect(uri.replace('https://','http://'))
                    self.response.out.write(result.content)
                else:
                    #记录一下Agent,准备干掉一批搜索引擎，节省流量。
                    logging.debug('User-Agent = %s ' % self.request.headers['User-Agent'])
                    self.response.out.write(self.replace(result.content,
                                                {remote_host:self.request.scheme + "://"+ self.request.host + '/',}
                                                ) + google_analytics)
            else:
                self.response.set_status(result.status_code)
                self.response.out.write(u'牛博国际拒绝了我的访问，请稍候再试<br/>status_code = %s' % result.status_code )
                logging.error('status_code = %s' % result.status_code )
                logging.error(url)
        except Exception,e:
            logging.exception(e)
            pass                    
        
    def replace(self,content,replace_str_dict={}):
            for k,v in replace_str_dict.items():
                content = content.replace(k,v)
            import re
            regx = r'(?P<tag>src=(\"|\'))(?P<url>/.*(\"|\'))'
            content = re.sub(regx,r'\g<tag>http://' + self.request.host + '\g<url>',unicode(content,'utf-8'))
            return content
    #残次品，暂时没有具体功能。
    def post(self):
        self.response.out.write(u'暂不支持提交功能，具体什么时候能行，问GFW客服.<a href="/">返回首页</a>')
        return
    
def main():
    application = webapp.WSGIApplication(
                                       [('/.*', MainPage),],
                                       debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()