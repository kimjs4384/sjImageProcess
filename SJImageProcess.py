# -*- coding: utf-8 -*-
from flask import Flask
from flask import request
from flask import Response
from flask import render_template
from flask import abort
from ImageProcess import ImageProcess

app = Flask(__name__)

@app.route("/test", methods=['GET'])
@app.route("/sjuniv/test", methods=['GET'])
def test():
    return 'test success'

@app.route("/image", methods=['GET'])
@app.route("/sjuniv/image", methods=['GET'])
def getRequestData():
    # TODO: 선택 파일(데이터), 영역정보
    # data는 년도 / Area는 GML 파일 명
    # data_1 = request.args.get('data_1', 'auto')
    # data_2 = request.args.get('data_2', 'auto')
    # dataArea = request.args.get('dataArea', 'auto')

    data_1 = '2007'
    data_2 = '2014'
    dataArea = 'clip_gml_4326'

    t = ImageProcess(data_1, data_2, dataArea)
    # t = ImageProcess()
    t.start()

    return 'success'

#############################
# 서비스 실행
if __name__ == '__main__':
    app.run(host='0.0.0.0')

# 기본 서비스로 실행시 flask 한 프로세스 당 1 요청만 처리할 수 있어 성능에 심각한 문제
# http://stackoverflow.com/questions/10938360/how-many-concurrent-requests-does-a-single-flask-process-receive

# Apache WSGI로 실행 필요
# http://flask-docs-kr.readthedocs.org/ko/latest/ko/deploying/mod_wsgi.html
# http://flask.pocoo.org/docs/0.10/deploying/mod_wsgi/
"""
### httpd.conf
# Call Python GeoCoding module by WSGI
LoadModule wsgi_module modules/mod_wsgi-py27-VC9.so
<VirtualHost *>
    ServerName localhost
    WSGIScriptAlias /sdmc d:\www_python\GRestApi\Gsdmc_rest_api.wsgi
    <Directory d:\www_python\GRestApi>
        Order deny,allow
        Require all granted
    </Directory>
</VirtualHost>
"""