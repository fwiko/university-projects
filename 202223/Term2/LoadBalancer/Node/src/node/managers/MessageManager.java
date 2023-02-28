/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package node.managers;

import java.io.IOException;
import static java.lang.Thread.interrupted;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.StandardProtocolFamily;
import java.nio.ByteBuffer;
import java.nio.channels.DatagramChannel;
import java.util.LinkedList;
import node.messages.MessageInbound;
import node.messages.MessageOutbound;

/**
 *
 * @author fwiko
 */
public class MessageManager {
    private static MessageManager instance;

    private Thread messageReceiver = null;
    private DatagramChannel datagramChannel = null;
    
    // Linked List data structure used to store yet to be processed Messages
    private LinkedList<MessageInbound> messageQueue;

    // Mutexes used to provide exclusive access to the messageQueue Linked List
    private final Object messageQueueLock = new Object();
    
    private MessageManager() {
        messageQueue = new LinkedList<>();
    }

    public static MessageManager getInstance() {
        if (instance != null) {
            return instance;
        }
        instance = new MessageManager();
        return instance;
    }
    
    public void start(InetAddress ipAddress, int portNumber) throws IOException {
            datagramChannel = DatagramChannel.open(StandardProtocolFamily.INET)
                    .bind(new InetSocketAddress(ipAddress, portNumber));
            datagramChannel.configureBlocking(false);
            receive();
    }

    private void receive() {
        messageReceiver = new Thread() {
            @Override
            public void run() {
                System.out.printf("Message Manager (Info): Listening for Messages on socket %s:%d\n", datagramChannel.socket().getLocalAddress(), datagramChannel.socket().getLocalPort());

                // While the Thread has not been stopped
                while (!interrupted()) {
                    ByteBuffer buffer = ByteBuffer.allocate(1024);

                    // Receive a Message through the Datagram Channel and store the contents in the buffer
                    try {
                        datagramChannel.receive(buffer);
                    } catch (IOException e) {
                        System.err.println("Message Manager (Error): IOException when receiving Message(s)");
                        messageReceiver.interrupt();
                    }

                    // Decode the Bytes stored in the buffer into a String and remove any white space
                    String messageString = new String(buffer.array()).trim();

                    // If the Message is not empty, create a new MessageInbound Object using "," as a separator
                    if (!messageString.isEmpty()) {
                        MessageInbound newMessage = new MessageInbound(messageString);
                        System.out.printf("Message Manager (Info): Received new %s Message\n", newMessage.getType().toString());
                        queueMessage(newMessage);
                    }
                }
            }
        };

        messageReceiver.start();
    }

    public void sendMessage(MessageOutbound message, InetAddress ipAddress, int portNumber){
        // Pack the MessageOutbound object into a single String value, convert it to a Byte-array and store it in a ByteBuffer
        byte[] messageBytes = message.packString().getBytes();
        ByteBuffer buffer = ByteBuffer.wrap(messageBytes);

        // Send the Message to the socket ipAddress:portNumber across the established Datagram Channel
        try {
            datagramChannel.send(buffer, new InetSocketAddress(ipAddress, portNumber));
        } catch (IOException e) {
            System.err.printf("Message Manager (Info): Failed to send %s Message to socket %s:%d\n", message.getType().toString(), ipAddress.getHostAddress(), portNumber);
            return;
        }
        
        System.out.printf("Message Manager (Info): Successfully sent %s Message to socket %s:%d\n", message.getType().toString(), ipAddress.getHostAddress(), portNumber);
    }

    private void queueMessage(MessageInbound message) {
        synchronized (messageQueueLock) {
            messageQueue.add(message);
        }
    }

    public MessageInbound getNextMessage() {
        synchronized (messageQueueLock) {
            return messageQueue.poll();
        }
    }

    public void stop() {
        messageReceiver.interrupt();
    }
}
