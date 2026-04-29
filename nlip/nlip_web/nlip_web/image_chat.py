from nlip_web.genai import StatefulGenAI
from nlip_web  import nlip_ext as nlip_ext 
from nlip_web.env import read_digits, read_string
from nlip_server import server
from nlip_sdk import nlip


class ChatApplication(nlip_ext.SafeStatefulApplication):
    def __init__(self):
        super().__init__()
        self.local_port = read_digits("LOCAL_PORT",8020)
        self.model = read_string("CHAT_MODEL", "nlip-test-model")
        self.host = read_string("CHAT_HOST", "localhost")
        self.port = read_digits("CHAT_PORT", 11434)
    

    def create_stateful_session(self) -> server.NLIP_Session:
        genAI = StatefulGenAI(self.host, self.port,self.model)
        session = ChatSession()
        session.set_correlator()
        self.store_session_data(session.get_correlator(), genAI)
        return session

    


class ChatSession(nlip_ext.StatefulSession):

    def execute(
        self, msg: nlip.NLIP_Message
    ) -> nlip.NLIP_Message:
        text = msg.extract_text()
        images = list()
        binary_contents = msg.extract_field_list("binary")
        for base64_content in binary_contents:
            images.append(base64_content)

        chat_server = self.nlip_app.retrieve_session_data(self.get_correlator())
        if chat_server is None: 
            return nlip.NLIP_Factory.create_text("Error: Can't find my chat server")

        # print(f'Received text {text[0:10]}...')
        response = chat_server.chat_multimodal(text, images = images)
        # print(f'Received response {response[0:10]}...')
        return nlip.NLIP_Factory.create_text(response)



if __name__ == "__main__":
    chatapp = ChatApplication()
    webapp = nlip_ext.WebApplication(indexFile="static/image_chat.html")
    app = webapp.setup_webserver(chatapp, port=chatapp.local_port)