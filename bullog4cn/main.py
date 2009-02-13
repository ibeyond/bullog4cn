# encoding=utf-8
import wsgiref.handlers
import logging
from google.appengine.ext import webapp
from google.appengine.api import urlfetch
from google.appengine.api import memcache

remote_host = 'http://www.bullogger.com/'
remote_favicon = remote_host + 'App_Themes/p_portal/images/shortcut.ico'

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
                        memcache.add(url,result,86400)
                    except:
                        pass
                    if result.headers['Content-Type'].find('image') != -1 and uri.find('https://') != -1:
                        self.redirect(uri.replace('https://','http://'))
                    self.response.out.write(result.content)
                else:
                    self.response.out.write(self.replace(result.content,
                                                {remote_host:'https://' + self.request.host + '/',}
                                                ) + google_analytics)
            else:
                self.response.set_status(result.status_code)
                logging.error('status_code = %s' % result.status_code )
                logging.error(url)
        except Exception,e:
            logging.exception(e)
            pass                    

    def replace(self,content,replace_str_dict={}):
            for k,v in replace_str_dict.items():
                content = content.replace(k,v)
            return content
        
    def post(self):
        uri = self.request.uri
        url_list = uri.split('/')
        
        url = (remote_host + '/'.join(url_list[3:]))
        try:
            import urllib
            form_fields = {}
            for k,v in self.request.POST.items():
                form_fields[k.encode('utf-8')] = v.encode('utf-8')
            form_data = urllib.urlencode(form_fields)
            result = urlfetch.fetch(url=url,
                                    payload=form_data,
                                    method=urlfetch.POST,
                                    headers=self.request.headers)
            if result.status_code == 200:
                self.response.headers['Content-Type'] = result.headers['Content-Type']
                self.response.out.write(self.replace(result.content,
                                            {remote_host:'https://' + self.request.host + '/',}
                                            ))
            else:
                self.response.out.write(u'暂不支持提交功能，具体什么时候能行，问GFW客服.<a href="/">返回首页</a>')
                logging.error('status_code = %s' % result.status_code )
                logging.error(url)
        except Exception,e:
            logging.exception(e)
            pass    
        
def main():
    application = webapp.WSGIApplication(
                                       [('/.*', MainPage),],
                                       debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()