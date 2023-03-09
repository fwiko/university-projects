package node.messages;

import java.util.Arrays;

public class Message {
    protected String instruction = "";
    private String[] parameters = null;

    public Message(String messageString) {
        String[] messageElements = messageString.split(",");
        instruction = messageElements[0];
        parameters = Arrays.copyOfRange(messageElements, 1, messageElements.length);
    }

    public String[] getParameters() {
        return parameters;
    }

    public String getParameter(int index) throws IndexOutOfBoundsException {
        if (index < 0 || index >= parameters.length) {
            throw new IndexOutOfBoundsException("Index out of Message parameter bounds");
        }
        return parameters[index];
    }

    public String packString() {
        return instruction + "," + String.join(",", parameters);
    }
}