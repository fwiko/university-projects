/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package loadbalancer.managers;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.util.LinkedList;
import loadbalancer.message.MessageInbound;
import loadbalancer.message.MessageOutbound;

/**
 *
 * @author fwiko
 */
public class MessageManager {
    private static MessageManager instance;
    
    private final LinkedList<MessageInbound> receivedMessages = new LinkedList<>();
    private Thread messageReceiver;
    private DatagramSocket serverSocket = null;
    private final Object mutexLock = new Object();
    
    public static MessageManager getInstance() {
        if (instance != null) {
            return instance;
        }
        instance = new MessageManager();
        return instance;
    }
    
    public void listen(DatagramSocket socket) {
        serverSocket = socket;
        receive();
    }
    
    private void receive() {
        // Create a new Thread used to receive/listen for Messages from Initiator and Node(s)
        messageReceiver = new Thread() {
            @Override
            public void run() {
                System.out.println(String.format("Message Manager (Info): Listening for Messages on %s:%d", serverSocket.getLocalAddress(), serverSocket.getLocalPort()));
                // While the Thread is not interrupted (stopped)
                while (!interrupted()) {
                    // Create a new Byte-array - 1024 Bytes in size (this should be large enough to accommodate any Message used in this system)
                    byte[] buffer = new byte[1024];
                    
                    // Attempt to receive a Message on the listener socket established by the Load-Balancer server
                    try {
                        serverSocket.receive(new DatagramPacket(buffer, buffer.length));
                    } catch (IOException e) {
                        System.out.println("Message Manager (Error): Issue receiving Message due to IOException");
                    }
                    
                    // Decode the received Bytes stored in the buffer into a String - remove any white space
                    String message = new String(buffer).trim();
                    
                    // If the Message is not empty, createa a new MessageInbound object, using "," as the separator character
                    if (message.length() > 0) {
                        addMessage(new MessageInbound(message, ","));
                    }
                }
            }
        };
        
        // Start the above messageListener Thread
        messageReceiver.start();
    }
    
    public void sendMessage(MessageOutbound message, InetAddress ipAddr, int portNum) {
        // "Pack" the MessageOutbound object into a string using "," as the separator
        byte[] messageBytes = message.packString(",").getBytes();
        
        // Attempt to create a new DatagramPacket object and send it to the specified IP and Port over the established socket
        try {
            DatagramPacket packet = new DatagramPacket(messageBytes, messageBytes.length, ipAddr, portNum);
            serverSocket.send(packet);
            System.out.println(String.format("Message Manager (Info): %s Message sent sucessfully", message.getType().toString()));
        } catch (IOException e) {
            System.out.println(String.format("Message Manager (Error): %s Message could not be sent", message.getType().toString()));
        }
    }
    
    private void addMessage(MessageInbound message) {
        // Use a Mutex to ensure exclusive access to the receivedMessages LinkedList
        synchronized (mutexLock) {
            // Add the new MessageInbound object to the receivedMessages LinkedList
            receivedMessages.add(message);
        }
    }
    
    public MessageInbound getNextMessage() {
        // Use a Mutex to ensure exclusive access to the receivedMessages LinkedList
        synchronized (mutexLock) {
            // Fetch, Return, and Remove the first item of the receivedMessages LinkedList
            return receivedMessages.pollFirst();
        }
    }
    
    public void stop() {
        // Interrupt (stop) the messageListener Thread
        messageReceiver.interrupt();
    }
}
