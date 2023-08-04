package loadbalancer.managers;

import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.StandardProtocolFamily;
import java.nio.ByteBuffer;
import java.nio.channels.DatagramChannel;
import java.util.LinkedList;
import loadbalancer.messages.MessageInbound;
import loadbalancer.messages.MessageOutbound;

public class MessageManager {
    // Value holding the singleton instance of the Message Manager
    private static MessageManager instance = null;
    
    // Thread used to receive Messages on the Datagram Channel
    private Thread messageReceiver = null;
    
    // Datagram Channel used to receive and send Messages
    private DatagramChannel datagramChannel = null;
    
    // LinkedList used to queue Messages in FIFO (First-In, First-Out) order
    private LinkedList<MessageInbound> messageQueue = null;
    
    // Mutex object to allow exclusive access to the "messageQueue" LinkedList
    private final Object messageQueueMutex = new Object();
    
    private MessageManager() {
        messageQueue = new LinkedList<>();
    }
    
    public static MessageManager getInstance() {
        // If there is no current instance of the Message Manager, create a new Instance
        if (instance == null) {
            instance = new MessageManager();
        }
        
        return instance;
    }
    
    public void start(InetAddress ipAddress, int portNumber) throws IOException {
        // Open a new Datagram Channel and bind to the specified IP Address and Port Number
        datagramChannel = DatagramChannel.open(StandardProtocolFamily.INET)
                .bind(new InetSocketAddress(ipAddress, portNumber));
        
        // Configure the Datagram Channel to non-blocking to allow for "easier" graceful shutdown
        datagramChannel.configureBlocking(false);
        
        // Start the message Receiving Thread
        receive();
    }
    
    public void sendMessage(MessageOutbound message, InetAddress ipAddress, int portNumber) {
        // Create a new ByteBuffer (similar to byte[]) and store the specified string inside as Bytes
        ByteBuffer buffer = ByteBuffer.wrap(message.toString().getBytes());
        
        // Attempt to send the contents of the ByteBuffer to the specified IP Address and Port Number across the Datagram Channel
        try {
            datagramChannel.send(buffer, new InetSocketAddress(ipAddress, portNumber));
        } catch (IOException exception) { // Handle an IOException occurring if the Message fails to send
            System.err.printf("MessageManager - ERROR: Failed to send %s Message to socket %s:%d", message.getType(), ipAddress.getHostAddress(), portNumber);
            return;
        }
        
        System.out.printf("MessageManager - INFO: Sent %s Message to socket %s:%d\n", message.getType(), ipAddress.getHostAddress(), portNumber);
    }
    
    public void stop() {
        // Interrupt (stop) the "messageReceiver" Thread
        messageReceiver.interrupt();
    }
    
    public boolean isStopped() {
        // Return TRUE if the "messageReceiver" Thread has been Interrupted (stopped)
        return messageReceiver.isInterrupted();
    }
    
    private void receive() {
        // Create a new Thread used to receive Messages from the Load-Balancer
        messageReceiver = new Thread() {
            @Override
            public void run() {
                System.out.printf("MessageManager - INFO: Listening for Messages on Socket %s:%s\n",datagramChannel.socket().getLocalAddress().getHostAddress(), datagramChannel.socket().getLocalPort());
                
                while (!Thread.currentThread().isInterrupted()) {
                    // Create a new ByteBuffer (similar to byte[]) and allocate 1024 Bytes
                    ByteBuffer buffer = ByteBuffer.allocate(1024);

                    // Attempt to receive a Message over the Datagram Channel and store it in "buffer"
                    try {
                        datagramChannel.receive(buffer);
                    } catch (IOException exception) { // Handle an IOException if receiving the Message on interface failed
                        messageReceiver.interrupt();
                        break;
                    }

                    // "Decode" the received Message bytes into a String and remove white space
                    String messageString = new String(buffer.array()).trim();

                    // If the Message String is empty, jump to the top of the loop
                    if (messageString.isEmpty()) { continue; }

                    // Create a new MessageInbound object with the contents of the received Message and add it to the Message Queue
                    MessageInbound message = new MessageInbound(messageString);

                    System.out.printf("MessageManager - INFO: Received %s Message\n", message.getType());

                    queueMessage(message);
                }
            }
        };
        
        // Start the above "messageReceiver" Thread
        messageReceiver.start();
    }
    
    private void queueMessage(MessageInbound message) {
        // Aquire the "messageQueueMutex" Mutex and add the given Message to the "messageQueue" LinkedList
        synchronized (messageQueueMutex) {
            messageQueue.add(message);
        }
    }
    
    public MessageInbound getNextQueuedMessage() {
        // Aquire the "messageQueueMutex" Mutex and "poll" (fetch and remove) the Message element at the front of the "messageQueue" LinkedList
        synchronized (messageQueueMutex) {
            return messageQueue.pollFirst();
        }
    }
}
