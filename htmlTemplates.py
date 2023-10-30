css = '''
<style>
.chat-message {
    padding: 0.5rem; border-radius: 1rem; margin-bottom: 1rem; display: flex;
}
.chat-message.user {
    background-color: #a6e0d2
}
.chat-message.bot {
    background-color: #f2f2f2
}
.chat-message .avatar img {
  max-width: 20px;
  max-height: 20px;
  border-radius: 50%;
  object-fit: cover;
}
.chat-message .message {
  padding: 0 1rem;
  color: #114041;
}

.stButton > button {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-top:26px;
    width: 100%;
    height: 100%;
    padding: 0.5em 1em;
    color: #FFFFFF;
    background-color: #007272;
    border-radius: 3px;
    text-decoration: none;
    cursor: pointer;
    border: none;
    font-size: 1rem;
    outline: none;
}
.stButton > button, .stButton > button a {
    color: #FFFFFF !important;
    text-decoration: none !important;
}
.stButton > button:hover,
.stButton > button:active,
.stButton > button:focus {
    background-color: #007272;
    color: #FFFFFF;
    text-decoration: none;
    box-shadow: none;
}
</style>
'''
expander = '''
<style>
[data-testid="stExpander"] div:has(>.streamlit-expanderContent) {
        max-height: 100px;
        overflow-y: auto;
    }
</style>
'''

bot_template = '''
<div class="chat-message bot" style="width: auto; display: flex; ">
    <div class="avatar">
        <img src="https://static.vecteezy.com/system/resources/previews/009/971/219/non_2x/chat-bot-icon-isolated-contour-symbol-illustration-vector.jpg" style="max-height: 20px; max-width: 20px; border-radius: 50%; object-fit: cover;">
    </div>
    <div class="message">{{MSG}}</div>
</div>
'''

user_template = '''
<div class="chat-message user" style="width: auto">
    <div class="avatar">
        <img src="https://static.vecteezy.com/system/resources/previews/016/009/835/original/the-human-icon-and-logo-vector.jpg">
    </div>    
    <div class="message">{{MSG}}</div>
</div>
'''