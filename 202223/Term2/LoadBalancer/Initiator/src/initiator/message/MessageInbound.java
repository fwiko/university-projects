/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package initiator.message;

import initiator.message.types.MessageTypeInbound;

/**
 *
 * @author fwiko
 */
public class MessageInbound extends Message {
    public MessageInbound(String messageString, String separator) {
        super(messageString, separator);
    }
    
    public MessageTypeInbound getType() {
        return MessageTypeInbound.valueOf(getParameter(0));
    }   
}
