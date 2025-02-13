import { useEffect, useRef } from "react";

const AgentChat = () => {
    // Reference for the chat container
    const chatContainerRef = useRef(null);

    // Scroll to the bottom whenever the chat content changes
    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, []);

    return (
        <div className="flex flex-col h-[500px] p-4">
            <h3 className="font-bold text-center mb-2">Chat:</h3>

            {/* Scrollable Chat Container */}
            <div
                ref={chatContainerRef}
                className="flex-1 overflow-y-auto overflow-x-hidden border border-gray-300 rounded-lg p-4 bg-gray-100 shadow-md"
            >
                <div className="space-y-3">
                    {/* Placeholder Messages */}
                    <div className="chat chat-start">
                        <div className="chat-bubble chat-bubble-neutral w-[500px]">
                            What is the capital of France?
                        </div>
                    </div>
                    <div className="chat chat-end">
                        <div className="chat-bubble chat-bubble-primary w-[500px]">
                            The capital of France is Paris.
                        </div>
                    </div>
                    <div className="chat chat-start">
                        <div className="chat-bubble chat-bubble-neutral w-[500px]">
                            Tell me a fun fact!
                        </div>
                    </div>
                    <div className="chat chat-end">
                        <div className="chat-bubble chat-bubble-primary w-[500px]">
                            Did you know that honey never spoils? Archaeologists found 3000-year-old honey that was still edible!
                        </div>
                    </div>
                    <div className="chat chat-start">
                        <div className="chat-bubble chat-bubble-neutral w-[500px]">
                            What is the capital of France?
                        </div>
                    </div>
                    <div className="chat chat-end">
                        <div className="chat-bubble chat-bubble-primary w-[500px]">
                            The capital of France is Paris.
                        </div>
                    </div>
                    <div className="chat chat-start">
                        <div className="chat-bubble chat-bubble-neutral w-[500px]">
                            Tell me a fun fact!
                        </div>
                    </div>
                    <div className="chat chat-end">
                        <div className="chat-bubble chat-bubble-primary w-[500px]">
                            Did you know that honey never spoils? Archaeologists found 3000-year-old honey that was still edible!
                        </div>
                    </div>
                </div>
            </div>

            {/* Chat Input */}
            <div className="mt-4 flex items-center">
                <input
                    type="text"
                    placeholder="Type your message..."
                    className="input input-bordered flex-1 p-2 border rounded-lg"
                />
                <button className="ml-2 btn btn-neutral">
                    Send
                </button>
            </div>
        </div>
    );
};

export default AgentChat;
