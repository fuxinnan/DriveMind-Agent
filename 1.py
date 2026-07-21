import os
from openai import OpenAI

# 注意: 不同地域的base_url不通用（下方示例使用北京地域的 base_url）
# - 华北2（北京）: https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1，请将{WorkspaceId}替换为业务空间ID
# - 新加坡: https://{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1
# - 德国（法兰克福）: https://{WorkspaceId}.eu-central-1.maas.aliyuncs.com/compatible-mode/v1
# - 日本（东京）: https://{WorkspaceId}.ap-northeast-1.maas.aliyuncs.com/compatible-mode/v1
# - 美国（弗吉尼亚）: https://dashscope-us.aliyuncs.com/compatible-mode/v1
client = OpenAI(
    api_key="sk-64a43951663e45ce884474669b62b21b",
    base_url="https://ws-r7c3vo4jw8ty5vqw.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
)
completion = client.chat.completions.create(
    model="qwen3.7-plus",
    messages=[{'role': 'user', 'content': '你是谁？'}]
)
print(completion.choices[0].message.content)