package loadbalancer.managers;

import java.io.IOException;
import static java.lang.Thread.interrupted;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.StandardProtocolFamily;
import java.nio.ByteBuffer;
import java.nio.channels.DatagramChannel;
import java.util.LinkedList;
import loadbalancer.messages.MessageInbound;
import loadbalancer.messages.MessageOutbound;

public class MessageManager {
    // Singleton instance of MessageManager
    private static MessageManager instance = null;
    
    // Thread used to receive Messages - to stop blocking
    private Thread messageReceiver = null;
    
    // DatagramChannel to send and receive datagram packets
    private DatagramChannel datagramChannel = null;
    
    // LinkedList of received Message objects yet to be handled
    private final LinkedList<MessageInbound> messageQueue;
    
    // Mutex object used for exclusive access to the messageQueue LinkedList
    private final Object messageQueueLock = new Object();
    
    private MessageManager() {
        messageQueue = new LinkedList<>();
    }

    public static MessageManager getInstance() {
        // If an instance of the MessageManager already exists
        if (instance != null) {
            return instance;
        }
        // Create a new instance of the MessageManager
        instance = new MessageManager();
        return instance;
    }
    
    public void start(InetAddress ipAddress, int portNumber) throws IOException {
        // Open the DatagramChannel and bind to the specified IP Address and Port Number of the Node
        datagramChannel = DatagramChannel.open(StandardProtocolFamily.INET)
                .bind(new InetSocketAddress(ipAddress, portNumber));
        // Set the DatagramChannel to non-blocking
        datagramChannel.configureBlocking(false);
        
        // Begin to receive Messages from the Load-Balancer
        receive();
    }

    private void receive() {
        messageReceiver = new Thread() {
            @Override
            public void run() {
                
                System.out.printf("     MessageManager - INFO: Listening for Messages on socket %s:%s\n", datagramChannel.socket().getLocalAddress().getHostAddress(), datagramChannel.socket().getLocalPort());
                
                // While the messageReceiver Thread has not been interrupted
                while (!interrupted()) {
                    // ByteBuffer object used to store up to 1024 Bytes of data (similar to byte[])
                    ByteBuffer buffer = ByteBuffer.allocate(1024);
                    
                    // Attempt to receive incoming Message through the DatagramChannel
                    try {
                        // Write the received Message contents to the buffer
                        datagramChannel.receive(buffer);
                    } catch (IOException e) {
                        System.out.println("     MessageManager - ERROR: IOException when receiving Message");
                        messageReceiver.interrupt();
                        break;
                    }
                    
                    // Convert the contents of the buffer to a String and remove white-space
                    String messageString = new String(buffer.array()).trim();
                    
                    // If the received Message is not empty
                    if (!messageString.isEmpty()) {
                        // Create a new Message object - passing in the received Message String
                        MessageInbound newMessage = new MessageInbound(messageString);
                        
                        System.out.printf("     MessageManager - INFO: Received %s Message\n", newMessage.getType().toString());
                        
                        // Add the received Message object to the messageQueue
                        queueMessage(newMessage);
                    }
                }
            }
        };
        
        // Start the messageReceiver Thread
        messageReceiver.start();
    }

    public void sendMessage(MessageOutbound message, InetAddress ipAddress, int portNumber){
        // Convert the Message object to a string, Encode it as Bytes and store it in the buffer
        ByteBuffer buffer = ByteBuffer.wrap(message.packString().getBytes());
        
        // Attempt to send the Message across the DatagramChannel datagramChannel to the specified IP Address and Port Number (Load-Balancer)
        try {
            datagramChannel.send(buffer, new InetSocketAddress(ipAddress, portNumber));
        } catch (IOException e) {
            System.err.printf("     MessageManager - ERROR: Failed to send %s Message to socket %s:%d\n", message.getType().toString(), ipAddress.getHostAddress(), portNumber);
            return;
        }
        
        System.out.printf("     MessageManager - INFO: Sent %s Message to socket %s:%d\n", message.getType().toString(), ipAddress.getHostAddress(), portNumber);
    }

    private void queueMessage(MessageInbound message) {
        // Activate (Lock) the messageQueue LinkedList Mutex object
        synchronized (messageQueueLock) {
            // Add the given Message object to the Message queue
            messageQueue.add(message);
        }
    }

    public MessageInbound getNextMessage() {
        // Activate (Lock) the messageQueue LinkedList Mutex object
        synchronized (messageQueueLock) {
            // Fetch the next Message object (first in list) from the Message queue
            return messageQueue.poll();
        }
    }

    public void stop() {
        // Interrupt (stop) the messageReceiver Thread
        messageReceiver.interrupt();
    }
    
    public boolean isStopped() {
        // Return true if the messageReceiver Thread has been interrupted
        return messageReceiver.isInterrupted();
    }
}