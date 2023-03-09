package node.messages;

import node.messages.types.MessageInboundType;

public class MessageInbound extends Message {
    public MessageInbound(String messageString) {
        super(messageString);
    }

    public MessageInboundType getType() {
        return MessageInboundType.valueOf(instruction);
    }
}