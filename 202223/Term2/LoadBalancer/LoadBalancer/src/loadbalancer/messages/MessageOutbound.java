package loadbalancer.messages;

import loadbalancer.messages.types.MessageOutboundType;

public class MessageOutbound extends Message {
    public MessageOutbound(MessageOutboundType instruction, String... parameters) {
        super(instruction + "," + String.join(",", parameters));
    }
    
    public MessageOutboundType getType() {
        // Get the instruction Enum value associated with the instruction String value
        return MessageOutboundType.valueOf(instruction);
    }   
}
