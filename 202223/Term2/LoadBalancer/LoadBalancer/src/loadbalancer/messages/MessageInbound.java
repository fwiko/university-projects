package loadbalancer.messages;

import loadbalancer.messages.types.MessageInboundType;

public class MessageInbound extends Message {
    public MessageInbound(String messageString) {
        super(messageString);
    }

    public MessageInboundType getType() {
        // Map the "instruction" string of the Message super-class to a value of the MessageInboundType enumerator
        return MessageInboundType.valueOf(instruction);
    }
}