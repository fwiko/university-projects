package loadbalancer.messages;

import loadbalancer.messages.types.MessageInboundType;

public class MessageInbound extends Message {
    public MessageInbound(String messageString) {
        super(messageString);
    }

    public MessageInboundType getType() {
        // Get the instruction Enum value associated with the instruction String value
        return MessageInboundType.valueOf(instruction);
    }
}
