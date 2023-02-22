/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package loadbalancer.messages;

import java.util.Arrays;

/**
 *
 * @author fwiko
 */
public class Message {
    private String messageInstruction = null;
    private String[] messageParameters = null;
    
    public Message(String messageString, String separator) {
        String[] params = messageString.split(separator);
        messageInstruction = params[0];
        messageParameters = Arrays.copyOfRange(params, 1, params.length);
    }
}
