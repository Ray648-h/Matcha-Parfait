# chat.py
# 新增：魔搭 Space 会自动注入 ZHIPU_API_KEY
from dotenv import load_dotenv
load_dotenv()  # 本地/.env 也兼容
import streamlit as st
from zhipuai import ZhipuAI
import os

# 页面配置
st.set_page_config(page_title="智谱清言聊天室", layout="centered")

@st.cache_resource
def get_client():
    return ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY", "f495802218b64531842c5006d7b6afc5.oX2u47xXY1LjPBOX"))  # 改成你的

client = get_client()

# 会话历史存在 Streamlit session_state
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 输入框
prompt = st.chat_input("请输入消息")
if prompt:
    # 1. 把用户消息加入历史并显示
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. 调智谱 API（流式）
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_reply = ""
        response = client.chat.completions.create(
            model="glm-4",
            messages=st.session_state.messages,
            stream=True
        )
        for chunk in response:
            delta = chunk.choices[0].delta
            if delta.content:
                full_reply += delta.content
                placeholder.markdown(full_reply)
        # 3. 把助手消息也加入历史
        st.session_state.messages.append({"role": "assistant", "content": full_reply})