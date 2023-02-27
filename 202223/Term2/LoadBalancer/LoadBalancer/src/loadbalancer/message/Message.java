/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package loadbalancer.message;

import java.util.Arrays;

/**
 *
 * @author fwiko
 */
public class Message {
    protected String instructionString = "";
    private String[] messageParameters = null;
    
    public Message(String messageString, String separator) {
        String[] messageElements = messageString.split(separator);
        instructionString = messageElements[0];
        messageParameters = Arrays.copyOfRange(messageElements, 1, messageString.length() + 1);
    }
    
    public String[] getParameters() {
        return messageParameters;
    }
    
    public String getParameter(int index) throws IndexOutOfBoundsException {
        if (index < 0 || index >= messageParameters.length) {
            throw new IndexOutOfBoundsException("Error: Index out of Message parameter bounds.");
        }
        return messageParameters[index];
    }
    
    public String packString(String separator) {
        return String.join(separator, messageParameters);
    }
}
