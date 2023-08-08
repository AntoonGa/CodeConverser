# -*- coding: utf-8 -*-
"""
Created on Sun Jul  2 12:56:21 2023

@author: agarc
TODO:
- currently, the loader only accepts files inside the working directory.
This is an issue with streamlit which only remembers filenames and not path (its a security thing)
So pass the text files I will probably have to load the files/text using streamlit and pass the string to the backend.
I would rather have the backend do the loading but Im not sure its possible... 
- Keep working on the speach vs text system which doesnt really atm. The system seems to be confused about whay output to send to the backend.
- test for stability. Sometime the system hangs, I cannot explain why yet.
- error handling
- a button to download history json
- add docstrings to each functions.
"""
import streamlit as st
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space
import chatbot_streamlit as chatbot_streamlit
import textwrap
import re
import time
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events

# =============================================================================
# text formating functions : these should be placed in a custom library
# =============================================================================
def separate_text_and_code(text: str) -> tuple:
    """
    Separates text and Python code from a string containing text and code
        enclosed by "```python" and "```".
    :param text: str, the input string containing text and code
    :return: tuple, a tuple containing two lists:
             1. A list of text and code segments in chronological order
             2. A list of metadata indicating whether the corresponding element
                 in the first list is code or text
    """
    pattern = r'(.*?)```python(.*?)```'
    segments = []
    metadata = []
    for match in re.finditer(pattern, text, re.DOTALL):
        text_segment, code_segment = match.groups()
        segments.append(text_segment.strip())
        metadata.append("text")
        segments.append(code_segment.strip())
        metadata.append("code")
    # if no segment is found we can exist the function
    if not segments:
        return [text], ["text"]
    # Append the remaining text after the last code block
    last_code_end = text.rfind("```")
    if last_code_end != -1:
        segments.append(text[last_code_end + 3:].strip())
        metadata.append("text")
    return segments, metadata


def wrap_code(code: str, width: int = 80) -> str:
    """
    Wrap long lines of code to the specified width.
    :param code: The code string to wrap.
    :type code: str
    :param width: The maximum width of a line, defaults to 80.
    :type width: int, optional
    :return: The wrapped code string.
    :rtype: str
    """
    # lines = repr(code).split('\\n')
    lines = code.split('\n')  # Changed from repr(code).split(\'\\\\')
    wrapped_lines = []
    for line in lines:
        stripped_line = line.lstrip()
        indent = len(line) - len(stripped_line)
        wrapped_line = textwrap.wrap(stripped_line, width=width - indent, break_long_words=False)
        wrapped_line = [f"{' ' * indent}{l}" if i == 0 else f"{' ' * (indent + 4)}{l}" for i, l in enumerate(wrapped_line)]
        wrapped_lines.extend(wrapped_line)
    wrapped_code = '\n'.join(wrapped_lines)
    return wrapped_code

def wrap_text(text: str, width: int = 80) -> str:
    """
    Wrap the given text to the specified width.
    :param text: str, the input text to wrap
    :param width: int, optional, the maximum width of a line, defaults to 80
    :return: str, the wrapped text
    /!\ sometimes html stuff gets wrongs (wrong linebrakes)
    """
    # text = html.escape(text)
    wrapped_text = textwrap.fill(text, width=width, replace_whitespace=False)
    return wrapped_text

def line_divider():
    """Stupid function to draw a line because I cant get it to work."""
    line = ["_" for ii in range(50)]
    
    return ''.join(line)

# =============================================================================
# streamlit control/interactions with the LLM
# =============================================================================
def flush_conversation():
    """
    Flush the conversation history in the Streamlit session state.
    This function clears the generated responses, past user inputs, and chatbot history.
    Everything happens in the llm backend
    """
    try:
        st.session_state['generated'] = [st.session_state['generated'][0]]
    except:
        pass

    try:
        st.session_state['past'] = [st.session_state['past'][0]]
    except:
        pass

    try:
        st.session_state['chatbot'].flush_history()
    except:
        pass
    return


def pop_conversation():
    try:
        st.session_state['generated'] = st.session_state['generated'][:-1]
    except:
        pass

    try:
        st.session_state['past'] = st.session_state['past'][:-1]
    except:
        pass

    try:
        st.session_state['chatbot']._pop_history()
    except:
        pass
    return
    

def generate_response(prompt, _chatbot): 
    """
    Generate a response from the chatbot based on the given prompt.
    :param prompt: str, the user input prompt
    :param _chatbot: chatbot_streamlit.llm instance, the chatbot object
    :return: str, the generated response from the chatbot
    The system can yield (backend), currently not usefull in the streamlit
    """
    response = ''
    for yielded in st.session_state['chatbot'].send_receive_message(prompt):
        response = response + yielded
        yield yielded
    return response

def update_context_tokens_display():
    """
    Update the display of context tokens in the Streamlit sidebar.
    This function calculates the number of context tokens in the chatbot's history
    and updates the display in the sidebar. (computation is in backend)
    """
    context_tokens = st.session_state['chatbot']._count_tokens_in_history()
    context_tokens_placeholder.write(f"Context tokens: {context_tokens}")
    return

def set_file_paths(user_paths):
    if not user_paths: pass
     
    user_paths = user_paths.split('\n')
    user_paths = [user_path.replace('"', '') for user_path in user_paths]
    # send the file_paths to the chatbot. This appends in the main loop and is always updated
    if st.session_state['chatbot'].system_role == "Python copilot":
        st.session_state["file_paths"] = user_paths
        st.session_state['chatbot'].add_context_py_file(st.session_state["file_paths"])
        print(*st.session_state["file_paths"])  

    pass

# =============================================================================
# Streamlit front end functions
# =============================================================================
def fetch_text():
    """
    Display a text area for user input and a button to clear the text area.
    :return: str, the user input text
    """
    input_text = st.text_area("Input", key="text")
    if input_text != st.session_state["last_user_input"] and input_text != st.session_state["text_input"]:  
        st.session_state["text_input_timestamp"] = time.time()
        return input_text
    else:
        return st.session_state["text_input"]

# second function for user input (paths)
def get_text_paths():
    """
    Display a text area for user input and a button to clear the text area.
    :return: str, the user input text
    """
    def clear_text():
        st.session_state["text"] = ""
        return

    input_text = st.text_area("Input path (separate by line breaks)", key="paths")
    # st.write(input_text)
    return input_text 

def display_response():
    # only get in touch with the llm if the user has inputed something new
    if st.session_state["user_input"] and st.session_state["user_input"] != st.session_state['last_user_input']:    
        # append a new instance of user question and answer
        st.session_state["generated"].append("")
        st.session_state['past'].append(st.session_state["user_input"])                  
        # save the new user input for the if statement
        st.session_state['last_user_input'] = st.session_state["user_input"]
        
        #get the chatbot response and place in st.session_state["generated"]
        response_generator = generate_response(st.session_state["user_input"], st.session_state['chatbot'])
        st.session_state["generated"][-1] = ''.join(response_generator) 
    
    # display if there is something to display.
    if len(st.session_state["generated"]) > 1:
        #create empty response_placeholders
        response_placeholders = []
        for _ in range(len(st.session_state["generated"])):
            response_placeholders.append(st.empty())
            
    
        #read chatbot messages and display in REVERSE order
        nb_of_exchanges = len(st.session_state["generated"])
        for ii in range(0, nb_of_exchanges):
            # select the last response
            response_to_print = st.session_state["generated"][ii]
            # display algorithm
            if response_to_print:
                try:
                    # separate text from code
                    segments, metadata = separate_text_and_code(response_to_print)
                    # prepare the response as an empty string
                    response_content = ""
                    for idx, segment in enumerate(segments):
                        # if segment is code we display as 
                        if metadata[idx] == "code":
                            # regex to find the code ```python <code> ```
                            response_content += f"```python\n{segment.strip()}\n```\n"
                        else:
                            # if text we just wrap it
                            wrapped_text = wrap_text(segment.strip())
                            response_content += f"{wrapped_text}\n"
                    # Add horizontal line to separate chatbot responses displays
                    response_content += '\n' + line_divider()
                    #display last response
                    response_placeholders[nb_of_exchanges-ii-1].markdown(response_content)
                    
                except:
                    pass
            else:
                pass

        


# =============================================================================
# SESSION STATE INIT
# =============================================================================
st.set_page_config(layout="wide")
if "init" not in st.session_state:
    st.session_state['init'] = True
    st.experimental_rerun()   
if 'chatbot' not in st.session_state:
    st.session_state['chatbot'] = chatbot_streamlit.llm()
    
if 'generated' not in st.session_state:
    st.session_state['generated'] = [""]
if 'past' not in st.session_state:
    st.session_state['past'] = [""]
    
if 'file_paths' not in st.session_state:
    st.session_state["file_paths"] = []  
    
if 'last_user_input' not in st.session_state:
    st.session_state['last_user_input'] = ''
if "user_input" not in st.session_state:   
    st.session_state["user_input"] = ''
if "speech_input" not in st.session_state:
    st.session_state["speech_input"] = ""
if "text_input" not in st.session_state:
    st.session_state["text_input"] = ""
    
if "speech_input_timestamp" not in st.session_state:
    st.session_state["speech_input_timestamp"] = 0
if "text_input_timestamp" not in st.session_state:
    st.session_state["text_input_timestamp"] = 0

    
else:
    st.session_state.init = False



# =============================================================================
# SIDEBAR CONTENT
# =============================================================================
with st.sidebar:
    st.title("🤗💬 Antoine chatbot Features:")
    
    # displays the number of tokens in the context
    context_tokens_placeholder = st.empty()
    
    # speech to text button
    stt_button = Button(label="Speak", width=4)  
    stt_button.js_on_event("button_click", CustomJS(code="""
        var recognition = new webkitSpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
    
        recognition.onresult = function (e) {
            var value = "";
            for (var i = e.resultIndex; i < e.results.length; ++i) {
                if (e.results[i].isFinal) {
                    value += e.results[i][0].transcript;
                }
            }
            if ( value != "") {
                document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
            }
        }
    
        recognition.start();
    
        function stopRecognition() {
            recognition.stop();
        }
    
        document.addEventListener('mouseup', stopRecognition);
        document.addEventListener('touchend', stopRecognition);
    """))  
    
    result = streamlit_bokeh_events(
        stt_button,
        events="GET_TEXT",
        key="listen",
        refresh_on_update=False,
        override_height=40,
        debounce_time=0)      

    # select the llm engine   
    add_vertical_space(2)
    option_engine = st.selectbox(
        'Engine',
        ('gpt4', 'gpt3'))
    if 'chatbot' in st.session_state and st.session_state['chatbot'].engine != option_engine:
        st.session_state['chatbot'].set_engine(option_engine)
        st.write(st.session_state['chatbot'].engine)

    # select the llm function
    add_vertical_space(2)
    option_system = st.selectbox(
        'System function',
        ("Python copilot", 'coder', 'commenter', 'chatbot', "dummy"))
    if 'chatbot' in st.session_state and st.session_state['chatbot'].system_function != option_system:
        st.session_state['chatbot'].set_system_function(option_system)
        st.write(st.session_state['chatbot'].system_function) 
     
    # delete history
    add_vertical_space(2)
    if st.button('Flush memory'):
        if 'chatbot' in st.session_state:
            st.write('Flushed')  # displayed when the button is clicked
            flush_conversation()            
    # pop history
    if st.button('Pop memory'):
        if 'chatbot' in st.session_state:
            st.write('Poped')  # displayed when the button is clicked
            pop_conversation()
            

         

# =============================================================================
# Layout of input/response containers
# =============================================================================
input_container = st.container()
colored_header(label='', description='', color_name='blue-30')
response_container = st.container()

with input_container:
    
    # path input for files
    user_paths = get_text_paths()
    set_file_paths(user_paths)
    # update context
    update_context_tokens_display()
    
    # Applying the user input box     
    st.session_state["text_input"] = fetch_text()
    
     

        
    

    
    if result:
        if "GET_TEXT" in result:
           new_speech_input = result.get("GET_TEXT")
           if new_speech_input != st.session_state["speech_input"] and new_speech_input != st.session_state["last_user_input"]:
               st.session_state["speech_input"] = new_speech_input
               st.session_state["speech_input_timestamp"] = time.time()




    with response_container:   
        # choose which respond to send, send the last one:
        if st.session_state["speech_input_timestamp"] >= st.session_state["text_input_timestamp"] :
            st.session_state["user_input"] = st.session_state['speech_input']
        else:
            st.session_state["user_input"] = st.session_state['text_input']
            
        if st.session_state["user_input"]:
            st.write(st.session_state["user_input"] + '\n' + line_divider())
            display_response()

    
    

     
# =============================================================================
# Conditional display of AI generated responses as a function of user provided prompts
# =============================================================================

    