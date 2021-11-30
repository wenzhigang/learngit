
"""
    Binance Websocket

"""

import json
import sys
import traceback
import socket
from datetime import datetime
from time import sleep
from threading import Lock, Thread    # 多线程模块
import websocket
import zlib

class BinanceWebsocket(object):
    """
        Websocket API
        创建Websocket client对象后，需要调用Start的方法去启动workder和ping线程
        1. Worker线程会自动重连.
        2. 使用stop方法去停止断开和销毁websocket client,
        3. 四个回调方法..
        * on_open
        * on_close
        * on_msg
        * on_error

        start()方法调用后，ping线程每隔60秒回自动调用一次。

    """

    def __init__(self, host=None, ping_interval=20):   #20s发一次ping
        """Constructor"""
        self.host = host   #服务器主机地址
        self.ping_interval = ping_interval  

        self._ws_lock = Lock()
        self._ws = None

        self._worker_thread = None
        self._ping_thread = None
        self._active = False  # 开启启动websocket的开关。

        # debug需要..
        self._last_sent_text = None
        self._last_received_text = None
        

    def start(self):
        """
        启动客户端，客户端连接成功后，会调用 on_open这个方法
        on_open 方法调用后，才可以向服务器发送消息的方法.
        """

        self._active = True
        self._worker_thread = Thread(target=self._run)   #启动工作的线程
        self._worker_thread.start()

        self._ping_thread = Thread(target=self._run_ping)  #启动ping的线程
        self._ping_thread.start()

    def stop(self):
        """
        停止客户端.
        """
        self._active = False
        self._disconnect()

    def join(self):
        """
        Wait till all threads finish.
        This function cannot be called from worker thread or callback function.
        """
        self._ping_thread.join()
        self._worker_thread.join()

    def send_msg(self, msg: dict):
        """
        向服务器发送数据.
        如果你想发送非json数据，可以重写该方法.
        """
        text = json.dumps(msg)
        self._record_last_sent_text(text)
        return self._send_text(text)

    def _send_text(self, text: str):
        """
        发送文本数据到服务器.
        """
        ws = self._ws
        if ws:
            ws.send(text, opcode=websocket.ABNF.OPCODE_TEXT)

    def _ensure_connection(self):
        """"""
        triggered = False  #临时变量
        with self._ws_lock:   
            if self._ws is None:   #假如ws为none，则websocket建立链接，并triggered设置为true
                self._ws = websocket.create_connection(self.host)

                triggered = True
        if triggered:
            self.on_open()

    def _disconnect(self):
        """
        """
        triggered = False
        with self._ws_lock:
            if self._ws:    #如果有数据，则置为空
                ws: websocket.WebSocket = self._ws
                self._ws = None

                triggered = True
        if triggered:
            ws.close()
            self.on_close()

    def _run(self):
        """
        保持运行，直到stop方法调用.
        """
        try:
            while self._active:
                try:
                    self._ensure_connection()   #循环一次后，如果没有连接，则连接
                    ws = self._ws
                    if ws:        #ws接收到数据发送给服务器
                        text = ws.recv()

                        # ws object is closed when recv function is blocking
                        if not text:   # ws如果没有数据或者出错，则断开。然后跳转到上面继续保证连接。
                            self._disconnect()
                            continue

                        self._record_last_received_text(text)

                        self.on_msg(text)   #如果收到数据，则跳转到on_msg去处理
                # ws is closed before recv function is called
                # For socket.error, see Issue #1608
                except (websocket.WebSocketConnectionClosedException, socket.error):
                    self._disconnect()

                # other internal exception raised in on_msg
                except:  # noqa
                    et, ev, tb = sys.exc_info()
                    self.on_error(et, ev, tb)
                    self._disconnect()  #

        except:  # noqa
            et, ev, tb = sys.exc_info()
            self.on_error(et, ev, tb)

        self._disconnect()

    def _run_ping(self):
        """"""
        while self._active:
            try:
                self._ping()
            except:  # noqa
                et, ev, tb = sys.exc_info()
                self.on_error(et, ev, tb)
                sleep(1)

            for i in range(self.ping_interval):
                if not self._active:
                    break
                sleep(1)

    def _ping(self):
        """"""
        ws = self._ws
        if ws:
            ws.send("ping", websocket.ABNF.OPCODE_PING)    #ws是方法，send是方法之一

    def on_open(self):
        """on open btc"""
        print("on open")
        data = {
                "method": "SUBSCRIBE",
                "params":
                [
                "btcusdt@markPrice@1s", "ethusdt@markPrice@1s","bnbusdt@markPrice@1s"
                ],
                "id": 1
                }
        self.send_msg(data)

    def on_close(self):
        """
        on close websocket
        """

    def on_msg(self, data: str):
        """call when the msg arrive."""
        # decompress = zlib.decompressobj(
        #     -zlib.MAX_WBITS  # see above
        # )

        msg = json.loads(data)
        print(msg)
        if 'table' in msg and msg['table'] == 'swap/depth5':
            data = msg['data']
            for item in data:
                bids = item["bids"]
                asks = item["asks"]
                print(asks)
                print("*"* 20)
                print(bids)

    def on_error(self, exception_type: type, exception_value: Exception, tb):
        """
        Callback when exception raised.
        """
        sys.stderr.write(
            self.exception_detail(exception_type, exception_value, tb)
        )

        return sys.excepthook(exception_type, exception_value, tb)

    def exception_detail(
            self, exception_type: type, exception_value: Exception, tb
    ):
        """
        Print detailed exception information.
        """
        text = "[{}]: Unhandled WebSocket Error:{}\n".format(
            datetime.now().isoformat(), exception_type
        )
        text += "LastSentText:\n{}\n".format(self._last_sent_text)
        text += "LastReceivedText:\n{}\n".format(self._last_received_text)
        text += "Exception trace: \n"
        text += "".join(
            traceback.format_exception(exception_type, exception_value, tb)
        )
        return text

    def _record_last_sent_text(self, text: str):
        """
        Record last sent text for debug purpose.
        """
        self._last_sent_text = text[:1000]

    def _record_last_received_text(self, text: str):
        """
        Record last received text for debug purpose.
        """
        self._last_received_text = text[:1000]


if __name__ == '__main__':
    Binance_ws = BinanceWebsocket(host="wss://fstream.binance.com/ws", ping_interval=20)
    Binance_ws.start()

