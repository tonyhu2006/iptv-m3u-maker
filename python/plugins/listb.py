#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tools
import time
import re
import db
import threading
import urllib.parse

class Source (object) :

    def __init__ (self):
        self.T = tools.Tools()
        self.now = int(time.time() * 1000)
        self.siteUrl = str('https://www.v2ex.com/member/Dotpy')

    def getSource (self) :
        urlList = []

        url = self.siteUrl
        req = [
            'user-agent: Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Mobile Safari/537.36',
        ]
        res = self.T.getPage(url, req)

        if res['code'] == 200 :
            pattern = re.compile(r"<li><a href=\"(.*?)\" data-ajax=\"false\">.*?<\/a><\/li>", re.I|re.S)
            postList = pattern.findall(res['body'])

            for post in postList :
                url = self.siteUrl + post
                req = [
                    'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
                ]
                res = self.T.getPage(url, req)

                if res['code'] == 200 :
                    pattern = re.compile(r"<li><a href=\"(.*?)\" data-ajax=\"false\">(.*?)<\/a><\/li>", re.I|re.S)
                    channelList = pattern.findall(res['body'])
                    threads = []

                    for channel in channelList :
                        channelUrl = self.siteUrl + channel[0]
                        thread = threading.Thread(target = self.detectData, args = (channel[1], channelUrl, ), daemon = True)
                        thread.start()
                        threads.append(thread)

                    for t in threads:
                        t.join()

                else :
                    pass # MAYBE later :P

    def detectData (self, title, url) :
        try:
            # Handle non-ASCII characters in title
            try:
                # Convert title to string and normalize it
                title = str(title)
                # Log with better error handling
                self.T.logger(f"Detecting data for: {title} at URL: {url}")
            except UnicodeEncodeError as e:
                # If title has encoding issues, use Unicode escapes
                escaped_title = title.encode('unicode_escape').decode('ascii')
                self.T.logger(f"Detecting data for title (escaped): {escaped_title} at URL: {url}")
            
            req = [
                'user-agent: Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Mobile Safari/537.36',
            ]
            
            playInfo = self.T.getPage(url, req)
            if not playInfo or playInfo['code'] != 200:
                self.T.logger(f"Failed to fetch page. Status: {playInfo.get('code') if playInfo else 'No response'}")
                return
                
            pattern = re.compile(r"<option value=\"(.*?)\">.*?<\/option>", re.I|re.S)
            playUrlList = pattern.findall(playInfo['body'])
            
            if len(playUrlList) > 0:
                playUrl = playUrlList[0]
                
                # Try to decode if it looks like base64
                if ';base64,' in playUrl:
                    import base64
                    try:
                        playUrl = base64.b64decode(playUrl.split(';base64,')[1]).decode('utf-8')
                    except Exception as e:
                        self.T.logger(f"Failed to decode base64 URL: {str(e)}")
                        return
                
                # URL validation and cleaning
                try:
                    # Remove any whitespace
                    playUrl = playUrl.strip()
                    
                    # Handle relative URLs
                    if not playUrl.startswith(('http://', 'https://')):
                        if playUrl.startswith('//'):
                            playUrl = 'http:' + playUrl
                        elif playUrl.startswith('/'):
                            playUrl = self.siteUrl.rstrip('/') + playUrl
                        else:
                            playUrl = self.siteUrl.rstrip('/') + '/' + playUrl
                    
                    # Parse and rebuild URL to ensure proper encoding
                    parsed = urllib.parse.urlparse(playUrl)
                    # Encode each component separately
                    path = urllib.parse.quote(parsed.path, safe='/:')
                    query = urllib.parse.quote(parsed.query, safe='=&')
                    fragment = urllib.parse.quote(parsed.fragment, safe='')
                    
                    # Rebuild URL with encoded components
                    playUrl = urllib.parse.urlunparse((
                        parsed.scheme,
                        parsed.netloc,
                        path,
                        parsed.params,
                        query,
                        fragment
                    ))
                    
                    print(f"detectData {title} {playUrl}")
                    self.addData({
                        'title': title,
                        'url': playUrl,
                        'quality': '',
                        'delay': 0,
                        'level': 0,
                        'cros': 0,
                        'retries': 0
                    })
                except Exception as e:
                    self.T.logger(f"Error processing URL {playUrl}: {str(e)}")
                    
        except Exception as e:
            self.T.logger(f"Error in detectData: {str(e)}")


    def addData (self, data) :
        DB = db.DataBase()
        sql = "SELECT * FROM %s WHERE url = '%s'" % (DB.table, data['url'])
        result = DB.query(sql)

        if len(result) == 0 :
            data['enable'] = 1
            DB.insert(data)
        else :
            id = result[0][0]
            DB.edit(id, data)
