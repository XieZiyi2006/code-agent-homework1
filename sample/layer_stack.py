"""分层协议栈示例，依据 homework1.docx 中的代码示例整理。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class Layer(ABC):
    def __init__(self, layer_no: int, name: str) -> None:
        self.layer_no = layer_no
        self.name = name
        self.upper_layer: Optional["Layer"] = None
        self.lower_layer: Optional["Layer"] = None

    def bind_upper(self, upper: "Layer") -> None:
        self.upper_layer = upper

    def bind_lower(self, lower: "Layer") -> None:
        self.lower_layer = lower

    def send(self, data: str) -> None:
        """接收上层 SDU，由本层封装后继续向下发送。"""
        print(f"[{self.name}] 收到上层 SDU: {data}，开始封装")
        self.send_down(self.encapsulate(data))

    def receive(self, pdu: str) -> None:
        """接收下层交付的 PDU，由本层解封装后继续向上交付。"""
        print(f"[{self.name}] 收到下层 PDU: {pdu}，开始解封装")
        self.deliver_up(self.decapsulate(pdu))

    def send_down(self, pdu: str) -> None:
        """把本层 PDU 作为下一层的 SDU，交给下一层继续封装。"""
        if self.lower_layer is None:
            print(f"[{self.name}] 无下层，PDU 丢弃: {pdu}")
            return
        self.lower_layer.send(pdu)

    def deliver_up(self, data: str) -> None:
        """把本层解封装得到的 SDU 交给上一层处理。"""
        if self.upper_layer is None:
            print(f"[{self.name}] 无上层，SDU 丢弃: {data}")
            return
        self.upper_layer.receive(data)

    @abstractmethod
    def encapsulate(self, sdu: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def decapsulate(self, pdu: str) -> str:
        raise NotImplementedError

    def error_notify(self, error_msg: str) -> None:
        print(f"[{self.name}] 差错通知：{error_msg}")
        if self.upper_layer:
            self.upper_layer.error_notify(f"下层报错：{error_msg}")

    def connect(self) -> None:
        print(f"[{self.name}] 建立连接")

    def disconnect(self) -> None:
        print(f"[{self.name}] 断开连接")


class AppLayer(Layer):
    def __init__(self) -> None:
        super().__init__(7, "应用层")

    def encapsulate(self, sdu: str) -> str:
        return f"[APP_PDU]{sdu}"

    def decapsulate(self, pdu: str) -> str:
        return pdu.replace("[APP_PDU]", "", 1)


class TransportLayer(Layer):
    def __init__(self) -> None:
        super().__init__(4, "传输层")

    def encapsulate(self, sdu: str) -> str:
        return f"[TCP_HDR]{sdu}"

    def decapsulate(self, pdu: str) -> str:
        return pdu.replace("[TCP_HDR]", "", 1)


class NetworkLayer(Layer):
    def __init__(self) -> None:
        super().__init__(3, "网络层")

    def encapsulate(self, sdu: str) -> str:
        return f"[IP_HDR]{sdu}"

    def decapsulate(self, pdu: str) -> str:
        return pdu.replace("[IP_HDR]", "", 1)


def build_stack() -> tuple[AppLayer, TransportLayer, NetworkLayer]:
    app, transport, network = AppLayer(), TransportLayer(), NetworkLayer()
    app.bind_lower(transport)
    transport.bind_upper(app)
    transport.bind_lower(network)
    network.bind_upper(transport)
    return app, transport, network


if __name__ == "__main__":
    app, _, network = build_stack()
    print("===== 发送流程 =====")
    app.send("Hello Network")
    print("===== 差错通知 =====")
    network.error_notify("IP 分组丢失")

