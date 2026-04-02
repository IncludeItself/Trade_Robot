from src.locks import ths_gui_operation_lock


def ths_gui_place_order(order):
    with ths_gui_operation_lock:
        pass

