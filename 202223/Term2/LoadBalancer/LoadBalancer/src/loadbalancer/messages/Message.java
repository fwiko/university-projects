package loadbalancer.messages;

import java.util.Arrays;

public class Message {
    // String representing the given instruction of the Message
    protected String instruction = "";
    
    // String-array holding any additional Message arguments
    private String[] arguments = null;

    public Message(String messageString) {
        String[] messageElements = messageString.split(",");
        instruction = messageElements[0];
        arguments = Arrays.copyOfRange(messageElements, 1, messageElements.length);
    }

    public String[] getArguments() {
        // Return the list of additional arguments
        return arguments;
    }

    public String getArgument(int index) throws IndexOutOfBoundsException {
        // If the given position is outside of the argument list bounds, throw an IndexOutOfBoundsException
        if (index < 0 || index >= arguments.length) {
            throw new IndexOutOfBoundsException("Index out of Message parameter bounds");
        }
        
        // Return the argument at the given position (0-indexed)
        return arguments[index];
    }

    @Override
    public String toString() {
        // "Pack" the Message values into a string with the instruction followed by any additional arguments 
        return instruction + (arguments.length > 0 ? "," + String.join(",", arguments) : "");
    }
}