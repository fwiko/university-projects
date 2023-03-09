package node.messages;

import node.messages.types.MessageOutboundType;

public class MessageOutbound extends Message {
    public MessageOutbound(MessageOutboundType instruction, String... parameters) {
        super(instruction + "," + String.join(",", parameters));
    }
    
    public MessageOutboundType getType() {
        return MessageOutboundType.valueOf(instruction);
    }   
}