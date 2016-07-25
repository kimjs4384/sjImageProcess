# -*- coding: utf-8 -*-
from flask import Flask
from flask import request
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
    # data는 년도 / Area는 GML 파일명
    # TODO: 데이터를 구분할 key 필요
    resId = request.args.get('id', 'auto')
    data_1 = request.args.get('data_1', 'auto')
    # data_1 = '2007'
    data_2 = request.args.get('data_2', 'auto')
    # data_2 = '2014'
    dataArea = request.args.get('dataArea', 'auto')
    # dataArea = 'A'

    t = ImageProcess(resId, data_1, data_2, dataArea)
    # t = ImageProcess()
    t.start()

    return 'success'

#############################
# 서비스 실행
if __name__ == '__main__':
    app.run(host='0.0.0.0')
