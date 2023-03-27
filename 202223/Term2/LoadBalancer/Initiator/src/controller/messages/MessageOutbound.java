package initiator.messages;

import initiator.messages.types.MessageOutboundType;

public class MessageOutbound extends Message {
    public MessageOutbound(MessageOutboundType instruction, String... parameters) {
        super(instruction + "," + String.join(",", parameters));
    }
    
    public MessageOutboundType getType() {
        // Map the "instruction" string of the Message super-class to a value of the MessageOutboundType enumerator
        return MessageOutboundType.valueOf(instruction);
    }   
}