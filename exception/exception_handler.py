from wecom.wecom import send_wecom_msg


def exception_handler(exc, context):
    send_wecom_msg(f"{context}：{exc}")