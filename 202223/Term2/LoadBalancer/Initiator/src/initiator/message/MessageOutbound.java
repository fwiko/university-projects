/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package initiator.message;

import initiator.message.types.MessageTypeOutbound;

/**
 *
 * @author fwiko
 */
public class MessageOutbound extends Message {
    public MessageOutbound(MessageTypeOutbound instruction, String separator, String... parameters) {
        super(instruction.toString() + separator + String.join(separator, parameters), separator);
    }
    
    public MessageTypeOutbound getType() {
        return MessageTypeOutbound.valueOf(getParameter(0));
    }   
}
