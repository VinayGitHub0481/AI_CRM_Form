import { useState, useRef, useEffect } from "react";
import axios from "axios";
import { Plus, Send, Loader2 } from "lucide-react";


/*this chatbot plays major role in updating the form fields based on the AI responses*/

function Chatbot({ updateFromAI }) {
  const [message, setMessage] = useState("");

  const [messages, setMessages] = useState([
    {
      sender: "ai",
      text: "Hello! I'm your AI Assistant. Tell me about your interaction with the HCP.",
    },
  ]);

  const [loading, setLoading] = useState(false);  /* here this function taken verifing  messages are loading  */

  const [uploading, setUploading] = useState(false);  /*here updating the state like uploading file */

  const fileInputRef = useRef(null);

  const bottomRef = useRef(null);

  // Replace with logged-in user's ID later
  const USER_ID = 1;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages]);

  //Here this function is used to decide 
  const sendMessage = async () => { 

  if (!message.trim() || loading) return;

  const currentMessage=message.trim();

  setMessages((prev) => [
    ...prev,{
      sender:"user",
      text:currentMessage,
    },
    ]);


  setMessage("");

  setLoading(true);

  try {

    const response = await axios.post(  /* here through this axios ,request sends to the backend llm model through  the api */
      "http://localhost:8000/chat",
      {
        user_id: USER_ID,
        user_query: currentMessage,
      }
    );

    console.log("Chat response",response.data);

    const aiText =
      response.data.chat_response ||
      response.data.response ||
      "Done";

    setMessages((prev) => [
      ...prev,
      {
        sender: "ai",
        text: aiText,       /* here ai message will be set to the setMessages function and state  gets updated */
      },
    ]);


    updateFromAI(response.data)


  } catch (err) {

    console.error(err);

    setMessages((prev) => [
      ...prev,
      {
        sender: "ai",
        text: "Something went wrong while contacting the server.",
      },
    ]);

  } finally {

    setLoading(false);   //closing the connections 

  }
};


/* Here uploading file taking place */
const handleFileUpload = async (e) => {
  const file = e.target.files[0];

  if (!file) return;

  setUploading(true);

  try {
    // Show user message
    setMessages((prev) => [
      ...prev,                              /* here ...prev means remebering the past conversation history */
      {
        sender: "user",
        text: `Uploaded: ${file.name}`,
      },
    ]);

    //here we are appending response to the formData 
    const formData = new FormData();

    formData.append("file", file);
    formData.append("user_id", USER_ID);

    const response = await axios.post(
      "http://localhost:8000/upload",
      formData,
    );

    const aiText =
      response.data.chat_response ||
      response.data.response ||
      `${file.name} processed successfully.`;

    // Show AI response
    setMessages((prev) => [
      ...prev,
      {
        sender: "ai",
        text: aiText,
      },
    ]);

    // Update HCP Form 

    updateFromAI(response.data)

  } catch (error) {
    console.error(error);

    setMessages((prev) => [
      ...prev,
      {
        sender: "ai",
        text: "Unable to process the uploaded file.",
      },
    ]);
  } finally {
    setUploading(false);

    // Allow selecting the same file again
    e.target.value = "";
  }
};




return (
  <div className="flex flex-col h-full bg-white rounded-lg border">

    {/* Header */}
    <div className="border-b p-5">
      <h2 className="text-lg font-semibold">
        AI Assistant
      </h2>
    </div>

    {/* Chat Area */}
    <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">

      {messages.map((msg, index) => (
        <div
          key={index}
          className={`flex ${
            msg.sender === "user"
              ? "justify-end"
              : "justify-start"
          }`}
        >
          <div
            className={`max-w-[75%] px-4 py-2 rounded-lg ${
              msg.sender === "user"
                ? "bg-blue-600 text-white"
                : "bg-gray-200 text-black"
            }`}
          >
            {msg.text}
          </div>
        </div>
      ))}

      {loading && (
        <p className="text-sm text-gray-500">
          AI is thinking...
        </p>
      )}

      {uploading && (
        <p className="text-sm text-gray-500">
          Uploading file...
        </p>
      )}

      <div ref={bottomRef}></div>

    </div>

    {/* Input Area */}
    <div className="border-t p-3 flex gap-2">

      {/* Upload Button */}
      <button
        onClick={() => fileInputRef.current.click()}
        className="border px-3 rounded hover:bg-gray-100"
      >
        +
      </button>

      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        onChange={handleFileUpload}
      />

      {/* Message Input */}
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            sendMessage();
          }
        }}
        placeholder="Describe the HCP interaction..."
        className="flex-1 border rounded px-3 py-2 outline-none"
      />

      {/* Send Button */}
      <button
        onClick={sendMessage}
        disabled={!message.trim() || loading}
        className="bg-blue-600 text-white px-4 rounded hover:bg-blue-700 disabled:bg-gray-400"
      >
        Send
      </button>

    </div>

  </div>
);


}

export default Chatbot;
